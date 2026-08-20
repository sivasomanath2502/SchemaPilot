"""
Phase 13 + Phase K/L/M: LangGraph orchestration.

  START -> Requirement -> Selection -> Schema (+MySQL validate/fix) -> Review
                                                                          |
                                                                     Problems?
                                                                     /      \
                                                                   YES       NO
                                                                    |         |
                                                                 Improve   ER Diagram -> Report -> END
                                                                    |
                                                                 (back to Review)

Loops at most 2 times (MAX_REVIEW_CYCLES) before finalizing and reporting
remaining issues honestly, rather than looping forever on an issue the
model can't resolve.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent / "agents"))

from langgraph.graph import StateGraph, END

from requirement_agent import run_requirement_agent
from selection_agent import run_selection_agent
from schema_agent_validated import run_schema_agent_validated
from review_agent import run_review_agent
from improve_agent import run_improve_step
from er_diagram_agent import run_er_diagram_agent
from report_agent import run_report_agent

MAX_REVIEW_CYCLES = 2


class GraphState(TypedDict):
    user_input: str
    requirement: dict
    selection: dict
    schema: dict
    review: dict
    cycle_count: int
    er_diagram: str
    report: dict


def requirement_step(state: GraphState) -> dict:
    print("\n=== Requirement Agent ===")
    result = run_requirement_agent(state["user_input"])
    return {"requirement": result.model_dump()}


def selection_step(state: GraphState) -> dict:
    print("\n=== Database Selection Agent ===")
    result = run_selection_agent(state["requirement"])
    return {"selection": result.model_dump()}


def schema_step(state: GraphState) -> dict:
    print("\n=== Schema Design Agent (+ MySQL validation) ===")
    result = run_schema_agent_validated(state["requirement"], state["selection"])
    return {"schema": result}


def review_step(state: GraphState) -> dict:
    print(f"\n=== Review Agent (cycle {state['cycle_count']}) ===")
    result = run_review_agent(state["requirement"], state["selection"], state["schema"])
    return {"review": result.model_dump()}


def improve_step(state: GraphState) -> dict:
    print(f"\n=== Improve (applying review feedback, cycle {state['cycle_count'] + 1}) ===")
    updated_schema = run_improve_step(state["schema"], state["review"])
    return {"schema": updated_schema, "cycle_count": state["cycle_count"] + 1}


def er_diagram_step(state: GraphState) -> dict:
    print("\n=== ER Diagram (deterministic, from validated DDL) ===")
    return {"er_diagram": run_er_diagram_agent(state["schema"])}


def report_step(state: GraphState) -> dict:
    print("\n=== Final Report Synthesis ===")
    return {"report": run_report_agent(
        state["requirement"], state["selection"], state["schema"],
        state["review"], state["er_diagram"],
    )}


def route_after_review(state: GraphState) -> str:
    critical_issues = [i for i in state["review"]["issues"] if i["severity"] == "critical"]
    if critical_issues and state["cycle_count"] < MAX_REVIEW_CYCLES:
        print(f"  -> {len(critical_issues)} critical issue(s) found, routing to Improve "
              f"(cycle {state['cycle_count'] + 1}/{MAX_REVIEW_CYCLES})")
        return "improve"
    if critical_issues:
        print(f"  -> {len(critical_issues)} critical issue(s) remain but max cycles "
              f"({MAX_REVIEW_CYCLES}) reached -- finalizing and reporting honestly")
    else:
        print("  -> No critical issues, finalizing")
    return "finalize"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("requirement_node", requirement_step)
    graph.add_node("selection_node", selection_step)
    graph.add_node("schema_node", schema_step)
    graph.add_node("review_node", review_step)
    graph.add_node("improve_node", improve_step)
    graph.add_node("er_diagram_node", er_diagram_step)
    graph.add_node("report_node", report_step)

    graph.set_entry_point("requirement_node")
    graph.add_edge("requirement_node", "selection_node")
    graph.add_edge("selection_node", "schema_node")
    graph.add_edge("schema_node", "review_node")
    graph.add_conditional_edges(
        "review_node", route_after_review,
        {"improve": "improve_node", "finalize": "er_diagram_node"},
    )
    graph.add_edge("improve_node", "review_node")
    graph.add_edge("er_diagram_node", "report_node")
    graph.add_edge("report_node", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    user_input = (
        "Design a database for an online ticket booking system. Users should be able "
        "to search events, select seats and book tickets. Multiple users may try to "
        "book the same seat simultaneously. Double booking must never occur."
    )

    final_state = app.invoke({
        "user_input": user_input,
        "requirement": {},
        "selection": {},
        "schema": {},
        "review": {},
        "cycle_count": 0,
        "er_diagram": "",
        "report": {},
    })
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    app_name = final_state.get("requirement", {}).get("application", "run").replace(" ", "_").lower()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"{app_name}_{timestamp}.json"
    out_path.write_text(json.dumps(final_state, indent=2), encoding="utf-8")
    print(f"\nFull result saved to: {out_path}")
    print("\n\n=== FINAL RESULT ===")
    print(json.dumps(final_state, indent=2))