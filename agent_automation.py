from typing import List, Dict, Any
from src.tools.declaration_details_retriever import fetch_declaration_details
from src.memory.agentstate import (
    RiskProfile,
    CDMInput,
    CDMExtracted,
    OrchestratorAgentState,
    CDMDecision
)
from src.workflow.cdm_graph import run_cdm_manager


def run_orchestrator(
    declaration_id: str,
    risk_profiles: List[RiskProfile]
) -> Dict[str, Any]:

    print("\n---> STARTING MULTI-RISK CDM AGENT FLOW\n")

    final_output: Dict[str, Any] = {
        "declaration_id": declaration_id,
        "results": []
    }

    # 1. Fetch Declaration Details (ONCE)
    try:
        declaration_details = fetch_declaration_details(declaration_id)
    except Exception as e:
        print(f"\n---> Failed to fetch declaration details: {e}")
        return final_output

    if not declaration_details or not declaration_details.hs_code:
        print("\n---> No HS Code found for this declaration ID")
        return final_output

    print("---> Declaration details fetched")
    print("HS Code:", declaration_details.hs_code)

    # 2. Process EACH Risk Independently
    for risk_profile in risk_profiles:

        print(f"\n---> Processing Risk ID: {risk_profile.risk_id}")

        # Create NEW CDM Input (per risk)
        cdm_input = CDMInput(
            declaration_id=declaration_id,
            risk_profile=risk_profile
        )

        # Task 1: Create NEW OrchestratorAgentState
        orch_state = OrchestratorAgentState(
            cdm_input=cdm_input,
            cdm_extracted=CDMExtracted(
                declaration_details=declaration_details
            ),
            cdm_decision=None
        )

        decision: CDMDecision | None = None

        try:
            orch_state = run_cdm_manager(orch_state)
            decision = orch_state.cdm_decision
        except Exception as e:
            print(f"---> CDM failed for risk {risk_profile.risk_id}: {e}")

        # Store Output (JSON-safe)
        final_output["results"].append({
            "risk_id": risk_profile.risk_id,
            "output": {
                "cdm_decision": decision.cdm_decision if decision else None,
                "cdm_feedback": decision.cdm_feedback if decision else None
            }
        })

        # Optional debug prints
        print(
            orch_state.tariff_feedback
            if hasattr(orch_state, "tariff_feedback")
            else "---> No tariff feedback available"
        )
        print(
            orch_state.valuation_feedback
            if hasattr(orch_state, "valuation_feedback")
            else "---> No valuation feedback available"
        )

        # Task 2: DELETE Orchestrator State
        del orch_state
        del decision

    print("\n---> MULTI-RISK CDM AGENT FLOW COMPLETED\n")
    return final_output
