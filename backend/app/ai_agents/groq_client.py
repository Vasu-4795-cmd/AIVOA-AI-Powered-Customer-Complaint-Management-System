import json
from groq import Groq

from app.config import settings

_client = Groq(api_key=settings.groq_api_key)


def call_groq(prompt: str, system: str = "", model: str | None = None,
              json_mode: bool = False, temperature: float = 0.2) -> str:
    """Thin wrapper around the Groq chat completions endpoint.

    - gemma2-9b-it is used as the default/fast model for most nodes.
    - llama-3.3-70b-versatile is used where we want more context/quality
      (e.g. root cause + CAPA reasoning), configurable via GROQ_MODEL_CONTEXT.
    """
    model = model or settings.groq_model_primary
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
        **kwargs,
    )
    return resp.choices[0].message.content


def call_groq_json(prompt: str, system: str = "", model: str | None = None) -> dict:
    raw = call_groq(prompt, system=system, model=model, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # gemma2-9b-it occasionally wraps JSON in prose/backticks - salvage it.
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise
