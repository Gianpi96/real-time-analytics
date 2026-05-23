from groq import Groq
from app.config import settings

_SYSTEM_PROMPT = (
    "You are an expert data analyst specializing in web analytics. "
    "Analyze the provided event data and deliver:\n"
    "1. Key traffic patterns and trends\n"
    "2. Anomalies or unusual spikes (be specific with numbers)\n"
    "3. Actionable recommendations for the product team\n"
    "Be concise, data-driven, and highlight the most impactful findings first."
)


def generate_insight_sync(summary: str) -> str:
    """Synchronous Groq call — intended for Celery workers."""
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this analytics summary:\n\n{summary}"},
        ],
        max_tokens=1024,
        temperature=0.6,
    )
    return response.choices[0].message.content
