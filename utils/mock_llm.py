"""Simple mock LLM used when OPENAI_API_KEY is not configured."""

from datetime import datetime


def ask(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return "Please provide a question."

    lowered = question.lower()
    if "deploy" in lowered or "deployment" in lowered:
        return (
            "Deployment is the process of releasing an application to a running "
            "environment so users can access it reliably."
        )

    return (
        f"Mock response at {datetime.utcnow().isoformat()}Z: "
        f"I received your question: {question}"
    )
