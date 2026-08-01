"""Builds the LangGraph StateGraphs used by the AI Copilot.

graph_extract  : raw uploaded text -> structured fields (populates the form)
graph_analyze  : structured fields -> completeness, risk, summary, root
                 cause, CAPA, duplicate detection (populates the AI Copilot /
                 Risk Assessment panel)
"""
from langgraph.graph import StateGraph, END

from app.ai_agents.nodes import (
    ComplaintState,
    extract_fields_node,
    completeness_checker_node,
    risk_classifier_node,
    summary_node,
    root_cause_node,
    capa_node,
    duplicate_detection_node,
)


def build_extract_graph():
    g = StateGraph(ComplaintState)
    g.add_node("extract_fields", extract_fields_node)
    g.set_entry_point("extract_fields")
    g.add_edge("extract_fields", END)
    return g.compile()


def build_analyze_graph():
    g = StateGraph(ComplaintState)
    g.add_node("completeness_checker", completeness_checker_node)
    g.add_node("risk_classifier", risk_classifier_node)
    g.add_node("summary", summary_node)
    g.add_node("root_cause_recommendation", root_cause_node)
    g.add_node("capa_recommendation", capa_node)
    g.add_node("duplicate_detection", duplicate_detection_node)

    g.set_entry_point("completeness_checker")
    # Sequential pipeline - each AI feature builds on the extracted fields.
    # root_cause -> capa is a real dependency (CAPA is generated from the
    # root cause hypotheses), the rest can be read as parallel AI Copilot
    # widgets but are run sequentially here for simplicity/traceability.
    g.add_edge("completeness_checker", "risk_classifier")
    g.add_edge("risk_classifier", "summary")
    g.add_edge("summary", "root_cause_recommendation")
    g.add_edge("root_cause_recommendation", "capa_recommendation")
    g.add_edge("capa_recommendation", "duplicate_detection")
    g.add_edge("duplicate_detection", END)
    return g.compile()


extract_graph = build_extract_graph()
analyze_graph = build_analyze_graph()
