from src.memory.agentstate import (
    OrchestratorAgentState,
    RiskProfile
)
from src.agents.tariff_verifier_agent import tariff_verifier_agent
from src.agents.valuation_verifier_agent import valuation_verifier_agent
#from langgraph import agent

#@agent(name="cdm_executor_agent", description="Execute tariff or valuation verification agents.")
def cdm_executor_agent(orch_data: OrchestratorAgentState) -> OrchestratorAgentState:
    """
    Executes a SINGLE risk profile in the OrchestratorAgentState.
    Routes based on risk_type:
    - TARIFF    → tariff_verifier_agent
    - VALUATION → valuation_verifier_agent
    """

    # Basic Validations
    if orch_data.cdm_input is None:
        raise ValueError("CDM Input missing in OrchestratorAgentState")

    risk_profile = orch_data.cdm_input.risk_profile
    if risk_profile is None:
        raise ValueError("Risk profile missing in CDM Input")

    if not isinstance(risk_profile, RiskProfile):
        raise ValueError("Invalid risk profile object")

    # Update Status
    orch_data.orchestrator_status = "EXECUTING"

    # Route Based on Risk Type
    risk_type = (risk_profile.risk_type or "").upper().strip()

    if risk_type == "TARIFF":
        tariff_verifier_agent(
            orch_data=orch_data,
            risk_profile=risk_profile
        )

    elif risk_type == "VALUATION":
        valuation_verifier_agent(
            orch_data=orch_data,
            risk_profile=risk_profile
        )

    else:
        print(f"[CDM EXECUTOR] Unknown risk_type: {risk_type}")

    # Execution Complete
    orch_data.orchestrator_status = "DECIDING"
    return orch_data
