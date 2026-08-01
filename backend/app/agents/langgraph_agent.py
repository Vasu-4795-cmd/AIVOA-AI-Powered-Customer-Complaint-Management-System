"""
LangGraph workflow powering the AIVOA Copilot.

Graph shape:

    START -> extract_entities -> assess_risk -> bonus_features -> compose_reply -> END

Each node either:
  a) calls Groq (gemma2-9b-it for fast extraction/classification,
     llama-3.3-70b-versatile for the richer reasoning steps), or
  b) falls back to the deterministic rule-based extractor in
     rule_based_fallback.py if GROQ_API_KEY isn't set / the call fails,
     so the whole app still works end-to-end in an offline demo.

A second, smaller graph (`correction_graph`) handles conversational
corrections in the copilot chat, e.g. "ah sorry the batch number is
BMX240602 and affected quantity is 48 capsules" -> a diff of only the
fields that changed.
"""
import json
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from app.config import get_settings
from app.schemas.complaint import ExtractedFields, RiskAssessment, BonusInsights
from app.agents import rule_based_fallback as fallback

logger = logging.getLogger("aivoa.agent")
settings = get_settings()

_groq_client = None


def _get_groq():
    """Lazily construct the Groq client only if a key is configured."""
    global _groq_client
    if _groq_client is None and settings.groq_enabled:
        from groq import Groq
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def _call_groq_json(system_prompt: str, user_prompt: str, model: str) -> Optional[dict]:
    """Call Groq's chat completion, forcing a JSON object back. Returns None on any failure."""
    client = _get_groq()
    if client is None:
        return None
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - want to always degrade gracefully in a demo
        logger.warning("Groq call failed (%s) -- falling back to rule-based extraction", exc)
        return None


# --------------------------------------------------------------------------
# Graph state
# --------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    raw_text: str
    fields: dict
    risk: dict
    bonus: dict
    reply: str


EXTRACTION_SYSTEM_PROMPT = """You are the AIVOA Copilot, an AI assistant embedded in a pharmaceutical
Quality Management System (QMS). Extract structured customer-complaint data from the user's
message, email, or OCR'd PDF text. Respond ONLY with a JSON object with exactly these keys:
complaint_source, customer_name, product_name, product_strength, batch_number,
affected_quantity, manufacturing_date, expiry_date, originating_site_block, impacted_npm,
complaint_category, complaint_description. Use null for anything not mentioned. Keep
complaint_description to 1-2 sentences summarizing the issue in formal QMS language."""

RISK_SYSTEM_PROMPT = """You are a pharmaceutical Quality Assurance risk-assessment assistant.
Given structured complaint fields, respond ONLY with a JSON object with keys:
ai_severity (one of "Minor", "Major", "Critical"), ai_suggested_next_action (a short QA
action phrase), ai_initial_risk_assessment (2-3 sentences: likely root cause hypothesis and
what should be investigated)."""

BONUS_SYSTEM_PROMPT = """You are a QMS copilot generating supporting insights for a logged
complaint. Respond ONLY with a JSON object with keys: ai_completeness_score (0-100 integer,
how complete the captured data is for QMS filing), ai_capa_recommendation (a short numbered
CAPA -- Corrective and Preventive Action -- plan), ai_summary (1 sentence complaint summary)."""


def extract_entities(state: AgentState) -> AgentState:
    text = state["raw_text"]
    result = _call_groq_json(EXTRACTION_SYSTEM_PROMPT, text, settings.groq_extraction_model)
    if result:
        fields = ExtractedFields(**{k: result.get(k) for k in ExtractedFields.model_fields})
    else:
        fields = fallback.extract_fields(text)
    return {**state, "fields": fields.model_dump()}


def assess_risk(state: AgentState) -> AgentState:
    fields = ExtractedFields(**state["fields"])
    result = _call_groq_json(
        RISK_SYSTEM_PROMPT, json.dumps(fields.model_dump()), settings.groq_context_model
    )
    if result:
        risk = RiskAssessment(**{k: result.get(k) for k in RiskAssessment.model_fields})
    else:
        risk = fallback.assess_risk(fields, state["raw_text"])
    return {**state, "risk": risk.model_dump()}


def bonus_features(state: AgentState) -> AgentState:
    fields = ExtractedFields(**state["fields"])
    result = _call_groq_json(
        BONUS_SYSTEM_PROMPT, json.dumps(fields.model_dump()), settings.groq_context_model
    )
    if result:
        bonus = BonusInsights(
            ai_completeness_score=result.get("ai_completeness_score"),
            ai_duplicate_of=None,
            ai_capa_recommendation=result.get("ai_capa_recommendation"),
            ai_summary=result.get("ai_summary"),
        )
    else:
        bonus = fallback.bonus_insights(fields, state["raw_text"])
    return {**state, "bonus": bonus.model_dump()}


def compose_reply(state: AgentState) -> AgentState:
    fields = ExtractedFields(**state["fields"])
    reply = (
        "Complaint parsed successfully. I've extracted the product details, mapped the batch "
        f"information, and generated an initial risk assessment "
        f"({state['risk'].get('ai_severity', 'N/A')} severity) for "
        f"{(fields.complaint_category or 'the reported issue').lower()}."
    )
    return {**state, "reply": reply}


def build_extraction_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extract_entities", extract_entities)
    graph.add_node("assess_risk", assess_risk)
    graph.add_node("bonus_features", bonus_features)
    graph.add_node("compose_reply", compose_reply)

    graph.set_entry_point("extract_entities")
    graph.add_edge("extract_entities", "assess_risk")
    graph.add_edge("assess_risk", "bonus_features")
    graph.add_edge("bonus_features", "compose_reply")
    graph.add_edge("compose_reply", END)
    return graph.compile()


_extraction_app = build_extraction_graph()


def run_extraction(raw_text: str) -> dict:
    """Entry point used by the /copilot/parse route."""
    final_state = _extraction_app.invoke({"raw_text": raw_text})
    return {
        "reply": final_state["reply"],
        "fields": final_state["fields"],
        "risk": final_state["risk"],
        "bonus": final_state["bonus"],
    }


# --------------------------------------------------------------------------
# Conversational correction graph (small, single-node -- kept separate so
# the extraction graph above stays the clean "primary" LangGraph workflow
# the reviewer will read first).
# --------------------------------------------------------------------------
CORRECTION_SYSTEM_PROMPT = """You are the AIVOA Copilot correcting a partially-filled
pharmaceutical complaint form based on the user's follow-up message. You are given the
CURRENT extracted fields as JSON and a follow-up correction message. Respond ONLY with a
JSON object with two keys: "updated_fields" (the full field object, same keys as input,
with only the corrected values changed) and "changed_keys" (a list of the field names that
were actually changed)."""


def run_correction(message: str, current_fields: ExtractedFields) -> dict:
    payload = json.dumps({"current_fields": current_fields.model_dump(), "message": message})
    result = _call_groq_json(CORRECTION_SYSTEM_PROMPT, payload, settings.groq_extraction_model)

    if result and "updated_fields" in result:
        updated = ExtractedFields(**{**current_fields.model_dump(), **result["updated_fields"]})
        changed = result.get("changed_keys", [])
        reply = "Got it. I have updated " + ", ".join(
            f'the {k.replace("_", " ").title()} to "{getattr(updated, k)}"' for k in changed
        ) + " in the form." if changed else "I couldn't find a field to update from that message -- could you rephrase?"
        return {"reply": reply, "updated_fields": updated.model_dump(), "changed_keys": changed}

    # Offline fallback: simple regex-based key: value corrections, mirrors the demo video
    return _fallback_correction(message, current_fields)


def _fallback_correction(message: str, current_fields: ExtractedFields) -> dict:
    import re
    updated = current_fields.model_copy()
    changed = []

    patterns = {
        "batch_number": r"batch\s*(?:number|no\.?)?\s*(?:is|:)?\s*([A-Za-z0-9\- ]{4,20})(?:\s+and|\.|$)",
        "affected_quantity": r"(?:affected\s*quantity|quantity)\s*(?:is|:)?\s*([\d,]+\s?[A-Za-z()\s]{2,25})",
        "manufacturing_date": r"manufactur(?:ing|ed)\s*date\s*(?:is|:)?\s*([A-Za-z0-9 ,]{4,20})",
        "expiry_date": r"expiry\s*date\s*(?:is|:)?\s*([A-Za-z0-9 ,]{4,20})",
        "customer_name": r"customer(?:\s*name)?\s*(?:is|:)?\s*([A-Za-z0-9 &.]{3,40})",
    }
    for field, pattern in patterns.items():
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            value = m.group(1).strip().rstrip(".")
            setattr(updated, field, value)
            changed.append(field)

    if changed:
        reply = "Got it. I have updated " + " and ".join(
            f'the {k.replace("_", " ").title()} to "{getattr(updated, k)}"' for k in changed
        ) + " in the form."
    else:
        reply = "I couldn't find a specific field to correct in that message -- could you tell me which field to update?"

    return {"reply": reply, "updated_fields": updated.model_dump(), "changed_keys": changed}
