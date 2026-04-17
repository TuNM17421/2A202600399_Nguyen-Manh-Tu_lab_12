"""Budget protection with Redis support and safe fallback."""
import logging
import time
from dataclasses import dataclass

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None

PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006


@dataclass
class UsageSnapshot:
    month: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    budget_usd: float


class CostGuard:
    def __init__(self, monthly_budget_usd: float = 10.0, warn_at_pct: float = 0.8):
        self.monthly_budget_usd = monthly_budget_usd
        self.warn_at_pct = warn_at_pct
        self._memory_usage: dict[str, dict] = {}
        self._redis = None

        if Redis and settings.redis_url:
            try:
                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Redis-backed cost guard enabled")
            except Exception as exc:
                logger.warning("Redis unavailable for cost guard, using memory fallback: %s", exc)
                self._redis = None

    @staticmethod
    def estimate_cost(input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

    def _month_key(self) -> str:
        return time.strftime("%Y-%m")

    def _warn_if_needed(self, cost_usd: float):
        if self.monthly_budget_usd > 0 and cost_usd >= self.monthly_budget_usd * self.warn_at_pct:
            pct = round(cost_usd / self.monthly_budget_usd * 100, 1)
            logger.warning("Budget usage is high: %s%% of monthly budget", pct)

    def check_and_record_usage(self, user_id: str, input_tokens: int, output_tokens: int) -> UsageSnapshot:
        added_cost = self.estimate_cost(input_tokens, output_tokens)

        if self._redis:
            try:
                return self._record_with_redis(user_id, input_tokens, output_tokens, added_cost)
            except Exception as exc:
                logger.warning("Redis cost guard failed, using memory fallback: %s", exc)

        return self._record_with_memory(user_id, input_tokens, output_tokens, added_cost)

    def _record_with_memory(self, user_id: str, input_tokens: int, output_tokens: int, added_cost: float) -> UsageSnapshot:
        month = self._month_key()
        state = self._memory_usage.setdefault(month, {"input": 0, "output": 0, "cost": 0.0, "users": {}})

        projected = state["cost"] + added_cost
        if projected > self.monthly_budget_usd:
            raise HTTPException(status_code=503, detail="Monthly budget exhausted. Try again next month.")

        state["input"] += input_tokens
        state["output"] += output_tokens
        state["cost"] = round(projected, 6)
        state["users"][user_id] = round(state["users"].get(user_id, 0.0) + added_cost, 6)
        self._warn_if_needed(state["cost"])

        return UsageSnapshot(month, state["input"], state["output"], state["cost"], self.monthly_budget_usd)

    def _record_with_redis(self, user_id: str, input_tokens: int, output_tokens: int, added_cost: float) -> UsageSnapshot:
        month = self._month_key()
        key = f"budget:{month}"
        user_key = f"budget:{month}:users"

        current_cost = float(self._redis.hget(key, "cost_usd") or 0.0)
        projected = current_cost + added_cost
        if projected > self.monthly_budget_usd:
            raise HTTPException(status_code=503, detail="Monthly budget exhausted. Try again next month.")

        pipeline = self._redis.pipeline()
        pipeline.hincrby(key, "input_tokens", input_tokens)
        pipeline.hincrby(key, "output_tokens", output_tokens)
        pipeline.hset(key, "cost_usd", round(projected, 6))
        pipeline.hincrbyfloat(user_key, user_id, added_cost)
        pipeline.expire(key, 60 * 60 * 24 * 35)
        pipeline.expire(user_key, 60 * 60 * 24 * 35)
        pipeline.execute()

        self._warn_if_needed(projected)
        input_total = int(self._redis.hget(key, "input_tokens") or 0)
        output_total = int(self._redis.hget(key, "output_tokens") or 0)
        return UsageSnapshot(month, input_total, output_total, round(projected, 6), self.monthly_budget_usd)

    def get_global_usage(self) -> dict:
        month = self._month_key()
        if self._redis:
            try:
                key = f"budget:{month}"
                return {
                    "month": month,
                    "input_tokens": int(self._redis.hget(key, "input_tokens") or 0),
                    "output_tokens": int(self._redis.hget(key, "output_tokens") or 0),
                    "monthly_cost_usd": float(self._redis.hget(key, "cost_usd") or 0.0),
                    "monthly_budget_usd": self.monthly_budget_usd,
                }
            except Exception:
                pass

        state = self._memory_usage.get(month, {"input": 0, "output": 0, "cost": 0.0})
        return {
            "month": month,
            "input_tokens": state.get("input", 0),
            "output_tokens": state.get("output", 0),
            "monthly_cost_usd": round(state.get("cost", 0.0), 6),
            "monthly_budget_usd": self.monthly_budget_usd,
        }


cost_guard = CostGuard(monthly_budget_usd=settings.monthly_budget_usd)
