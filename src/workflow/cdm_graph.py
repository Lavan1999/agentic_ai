# cdm_manager.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Orchestrator state
from src.memory.agentstate import OrchestratorAgentState

# Nodes
from src.tools.data_retriever import fetch_tariff_data, fetch_valuation_data
from src.agents.cdm_executor_agent import cdm_executor_agent
from src.agents.cdm_decision_agent import cdm_decision_agent


# LangGraph state wrapper
class GraphState(TypedDict):
    orch: OrchestratorAgentState


# NODE: DATA RETRIEVER
def retriever_node(state: GraphState):
    print("---> RUNNING DATA RETRIEVER NODE")
    orch = state["orch"]

    # Fetch Tariff based on declaration
    hs_code = None
    if orch.cdm_extracted and orch.cdm_extracted.declaration_details:
        hs_code = orch.cdm_extracted.declaration_details.hs_code

    if hs_code:
        orch = fetch_tariff_data(hs_code, orch)
        orch = fetch_valuation_data(hs_code, orch)
    else:
        print("[DATA RETRIEVER] No HS code found in declaration.")

    state["orch"] = orch
    return state


# NODE: CDM EXECUTOR
def executor_node(state: GraphState):
    print("---> RUNNING CDM EXECUTOR NODE")
    orch = state["orch"]
    orch = cdm_executor_agent(orch)
    state["orch"] = orch
    return state


# NODE: CDM DECISION
def decision_node(state: GraphState):
    print("---> RUNNING CDM DECISION NODE")
    orch = state["orch"]
    orch = cdm_decision_agent(orch)
    state["orch"] = orch
    return state


# BUILD LANGGRAPH WORKFLOW
def build_cdm_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retriever_node)
    workflow.add_node("execute", executor_node)
    workflow.add_node("decide", decision_node)

    # Set execution order
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "execute")
    workflow.add_edge("execute", "decide")
    workflow.add_edge("decide", END)

    return workflow.compile()


# RUN WORKFLOW
def run_cdm_manager(orch_state: OrchestratorAgentState) -> OrchestratorAgentState:
    app = build_cdm_workflow()
    result = app.invoke({"orch": orch_state})
    return result["orch"]
