from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.coordinator import detect_intent, route_message
from app.memory.patient_memory import store_interaction
from app.utils.constants import (
    INTENT_BOOK,
    INTENT_GENERAL,
    INTENT_RECORDS,
    INTENT_REMINDER,
    INTENT_SEARCH,
    INTENT_SUMMARY,
)


class HealthcareState(TypedDict):
    message: str
    patient_id: int
    intent: str
    response: str


def classify_node(state: HealthcareState) -> HealthcareState:
    intent = detect_intent(state["message"])
    return {**state, "intent": intent}


def _make_agent_node(intent_key: str):
    def node(state: HealthcareState) -> HealthcareState:
        if state["intent"] != intent_key:
            return state
        result = route_message(state["message"], state["patient_id"])
        return {**state, "response": result["response"]}
    return node


def general_node(state: HealthcareState) -> HealthcareState:
    if state["intent"] != INTENT_GENERAL:
        return state
    result = route_message(state["message"], state["patient_id"])
    return {**state, "response": result["response"]}


def memory_node(state: HealthcareState) -> HealthcareState:
    if state.get("response"):
        store_interaction(state["patient_id"], state["message"], state["response"])
    return state


def route_after_classify(state: HealthcareState) -> str:
    mapping = {
        INTENT_SEARCH: "search",
        INTENT_BOOK: "schedule",
        INTENT_RECORDS: "records",
        INTENT_REMINDER: "reminder",
        INTENT_SUMMARY: "summary",
        INTENT_GENERAL: "general",
    }
    return mapping.get(state["intent"], "general")


def build_healthcare_graph():
    graph = StateGraph(HealthcareState)
    graph.add_node("classify", classify_node)
    graph.add_node("search", _make_agent_node(INTENT_SEARCH))
    graph.add_node("schedule", _make_agent_node(INTENT_BOOK))
    graph.add_node("records", _make_agent_node(INTENT_RECORDS))
    graph.add_node("reminder", _make_agent_node(INTENT_REMINDER))
    graph.add_node("summary", _make_agent_node(INTENT_SUMMARY))
    graph.add_node("general", general_node)
    graph.add_node("memory", memory_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "search": "search",
            "schedule": "schedule",
            "records": "records",
            "reminder": "reminder",
            "summary": "summary",
            "general": "general",
        },
    )
    for node in ("search", "schedule", "records", "reminder", "summary", "general"):
        graph.add_edge(node, "memory")
    graph.add_edge("memory", END)

    return graph.compile()


_healthcare_graph = None


def run_healthcare_workflow(message: str, patient_id: int = 1) -> dict:
    global _healthcare_graph
    if _healthcare_graph is None:
        _healthcare_graph = build_healthcare_graph()

    initial: HealthcareState = {
        "message": message,
        "patient_id": patient_id,
        "intent": "",
        "response": "",
    }
    final = _healthcare_graph.invoke(initial)
    return {
        "intent": final["intent"],
        "response": final["response"],
        "patient_id": patient_id,
    }
