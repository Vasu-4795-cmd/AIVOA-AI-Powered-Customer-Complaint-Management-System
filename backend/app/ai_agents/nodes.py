"""LangGraph node functions for the Customer Complaint AI Copilot.

Each node takes the shared graph `state` dict, calls Groq (gemma2-9b-it by
default, llama-3.3-70b-versatile for the heavier reasoning nodes), and writes
its result back into `state`. Every node also appends a ComplaintEvent-style
trace entry to state["trace"] so the full end-to-end run can be shown/demoed.
"""
import json
from typing import TypedDict, List, Optional

from app.ai_agents.groq_client import call_groq_json, call_groq
from app.config import settings


class ComplaintState(TypedDict, total=False):
    raw_text: str
    fields: dict                 # extracted / user-submitted structured fields
    existing_complaints: List[dict]  # brief records used for duplicate detection

    completeness_score: float
    missing_fields: List[str]
    risk_level: str
    risk_rationale: str
    summary: str
    root_cause_suggestions: List[str]
    capa_suggestions: List[str]
    duplicate_of: Optional[str]
    duplicate_score: Optional[float]

    trace: List[dict]


def _trace(state: ComplaintState, node: str, output) -> None:
    state.setdefault("trace", []).append({"node": node, "output": output})


REQUIRED_FIELDS = [
    "customer_name", "product_name", "batch_lot_number",
    "complaint_category", "complaint_description", "manufacturing_site",
]


# ---------------------------------------------------------------------
# 1. Field extraction (used when a PDF/email/image is uploaded, to
#    auto-populate the "Log Customer Complaint" form)
# ---------------------------------------------------------------------
def extract_fields_node(state: ComplaintState) -> ComplaintState:
    system = (
        "You are an information-extraction assistant for a pharmaceutical "
        "Quality Management System (QMS) customer complaint intake module. "
        "Extract structured fields from raw complaint text (email body or "
        "text scraped from a PDF/image). Respond ONLY with a JSON object."
    )
    prompt = f"""
Extract the following fields from the complaint text below. If a field is not
present, set it to null. Use your best judgement for complaint_category
(one of: Quality Defect, Packaging Defect, Adverse Event, Efficacy/Performance,
Labeling, Delivery/Logistics, Other).

Fields: customer_name, customer_email, product_name, batch_lot_number,
complaint_category, complaint_description (a clean 2-4 sentence restatement
of the issue), manufacturing_site.

Complaint text:
\"\"\"{state['raw_text']}\"\"\"

Return JSON with exactly these keys: customer_name, customer_email,
product_name, batch_lot_number, complaint_category, complaint_description,
manufacturing_site.
"""
    data = call_groq_json(prompt, system=system, model=settings.groq_model_primary)
    state["fields"] = data
    _trace(state, "extract_fields", data)
    return state


# ---------------------------------------------------------------------
# 2. Complaint Completeness Checker
# ---------------------------------------------------------------------
def completeness_checker_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    score = round((len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS) * 100, 1)

    state["completeness_score"] = score
    state["missing_fields"] = missing
    _trace(state, "completeness_checker", {"score": score, "missing_fields": missing})
    return state


# ---------------------------------------------------------------------
# 3. AI Risk Classification
# ---------------------------------------------------------------------
def risk_classifier_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    system = (
        "You are a pharmaceutical Quality/Regulatory risk assessment expert. "
        "Classify the patient/product risk of a customer complaint per typical "
        "QMS severity criteria (consider: adverse events, contamination, "
        "potency/efficacy failure, mislabeling that could cause dosing error, "
        "vs. minor cosmetic/packaging issues). Respond ONLY with JSON."
    )
    prompt = f"""
Complaint details:
Product: {fields.get('product_name')}
Batch/Lot: {fields.get('batch_lot_number')}
Category: {fields.get('complaint_category')}
Description: {fields.get('complaint_description')}

Classify risk_level as one of: Low, Medium, High, Critical.
Give a 1-2 sentence risk_rationale explaining why, referencing patient safety,
regulatory reporting obligations (e.g. potential FDA MedWatch / adverse event
reporting), or product quality impact where relevant.

Return JSON: {{"risk_level": "...", "risk_rationale": "..."}}
"""
    data = call_groq_json(prompt, system=system, model=settings.groq_model_context)
    state["risk_level"] = data.get("risk_level", "Medium")
    state["risk_rationale"] = data.get("risk_rationale", "")
    _trace(state, "risk_classifier", data)
    return state


# ---------------------------------------------------------------------
# 4. Complaint Summary
# ---------------------------------------------------------------------
def summary_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    prompt = f"""
Summarize this pharmaceutical customer complaint in 2 concise sentences for a
QMS reviewer, suitable to display on a complaint dashboard card.

Product: {fields.get('product_name')}
Category: {fields.get('complaint_category')}
Description: {fields.get('complaint_description')}
"""
    summary = call_groq(prompt, model=settings.groq_model_primary).strip()
    state["summary"] = summary
    _trace(state, "summary", summary)
    return state


# ---------------------------------------------------------------------
# 5. Root Cause Recommendation
# ---------------------------------------------------------------------
def root_cause_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    system = (
        "You are a pharmaceutical manufacturing quality investigator familiar "
        "with API and Finished Dosage Form (FDF) processes, and common root "
        "cause frameworks (5-Why, fishbone: Man/Machine/Material/Method/"
        "Environment). Respond ONLY with JSON."
    )
    prompt = f"""
Complaint category: {fields.get('complaint_category')}
Description: {fields.get('complaint_description')}
Product: {fields.get('product_name')} | Batch: {fields.get('batch_lot_number')}

Suggest the 3 most probable root cause hypotheses an investigator should check
first, ordered by likelihood, phrased as short actionable investigation leads.

Return JSON: {{"root_causes": ["...", "...", "..."]}}
"""
    data = call_groq_json(prompt, system=system, model=settings.groq_model_context)
    state["root_cause_suggestions"] = data.get("root_causes", [])
    _trace(state, "root_cause_recommendation", data)
    return state


# ---------------------------------------------------------------------
# 6. CAPA Recommendation
# ---------------------------------------------------------------------
def capa_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    root_causes = state.get("root_cause_suggestions", [])
    system = (
        "You are a QMS specialist drafting CAPA (Corrective and Preventive "
        "Action) recommendations for a pharmaceutical manufacturer. Respond "
        "ONLY with JSON."
    )
    prompt = f"""
Complaint category: {fields.get('complaint_category')}
Description: {fields.get('complaint_description')}
Likely root causes: {root_causes}

Suggest 3 CAPA actions: mix of immediate corrective actions and longer-term
preventive actions. Keep each under 20 words.

Return JSON: {{"capa_actions": ["...", "...", "..."]}}
"""
    data = call_groq_json(prompt, system=system, model=settings.groq_model_context)
    state["capa_suggestions"] = data.get("capa_actions", [])
    _trace(state, "capa_recommendation", data)
    return state


# ---------------------------------------------------------------------
# 7. Duplicate Complaint Detection
# ---------------------------------------------------------------------
def duplicate_detection_node(state: ComplaintState) -> ComplaintState:
    fields = state.get("fields", {})
    candidates = state.get("existing_complaints", [])

    if not candidates:
        state["duplicate_of"] = None
        state["duplicate_score"] = None
        _trace(state, "duplicate_detection", "no existing complaints to compare")
        return state

    system = (
        "You detect duplicate/related pharmaceutical customer complaints by "
        "comparing product, batch/lot, and description similarity. Respond "
        "ONLY with JSON."
    )
    prompt = f"""
New complaint:
Product: {fields.get('product_name')} | Batch: {fields.get('batch_lot_number')}
Description: {fields.get('complaint_description')}

Existing complaints (id, product, batch, description):
{json.dumps(candidates, indent=2)}

If one existing complaint is very likely describing the same underlying issue
(same product/batch and similar description), return its id and a similarity
score 0-1. Otherwise return duplicate_of null and score 0.

Return JSON: {{"duplicate_of": "<id or null>", "score": <0-1 float>}}
"""
    data = call_groq_json(prompt, system=system, model=settings.groq_model_primary)
    duplicate_of = data.get("duplicate_of")
    valid_ids = {c["id"] for c in candidates}
    # Guard against the model hallucinating an id that wasn't in the candidate
    # list we gave it - only trust ids we actually sent it.
    if duplicate_of not in valid_ids:
        duplicate_of = None
    state["duplicate_of"] = duplicate_of
    state["duplicate_score"] = data.get("score", 0) if duplicate_of else 0
    _trace(state, "duplicate_detection", data)
    return state
