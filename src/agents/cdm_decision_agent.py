from typing import Optional
import requests
from config import OLLAMA_URL, MODEL_NAME
from src.memory.agentstate import (
    OrchestratorAgentState,
    CDMDecision,
    TariffFeedback,
    ValuationFeedback
)
#from langgraph import agent
from src.utils.client_llm import llm


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return ""
    return str(status).strip().upper()

#@agent(name="cdm_decision_agent", description="Make final CDM decision based on verifier feedback.")
def cdm_decision_agent(orch_data: OrchestratorAgentState) -> OrchestratorAgentState:
    """
    CDM FINAL DECISION NODE (Single risk profile only)

    - Uses rule-based mapping FIRST
    - LLM is used ONLY for explanation
    - Stores final decision in orch_data.cdm_decision
    """

    print("[CDM DECISION NODE] Executing")

    decision = orch_data.cdm_decision
    if decision is None:
        raise ValueError("CDMDecision missing in OrchestratorAgentState")

    # Pick whichever feedback exists
    feedback: Optional[TariffFeedback | ValuationFeedback] = (
        decision.tariff_feedback
        if decision.tariff_feedback
        else decision.valuation_feedback
    )

    if feedback is None:
        decision.cdm_decision = "INVALID HS CODE"
        decision.cdm_feedback = "No verifier feedback available; HS code may be invalid."
        orch_data.orchestrator_status = "DECIDING"
        return orch_data

    status = _normalize_status(feedback.status)

    # RULE-BASED DECISION
    if "UNDER" in status or "OVER" in status:
        final_decision = "CORRECTION"

    elif "INVALID" in status or "INCORRECT HS" in status or "NO DATA" in status:
        final_decision = "INVALID HS CODE"

    elif "ACCEPT" in status:
        final_decision = "ACCEPTED"

    elif "NEED REVIEW" in status or "ERROR" in status:
        final_decision = "NEED REVIEW"

    else:
        final_decision = None  # fallback to LLM

    # LLM FOR EXPLANATION (RULE HIT)
    if final_decision:
        try:
            prompt = f"""
                    You are a senior customs officer.

                    Verifier Status:
                    {feedback.status}

                    Verifier Explanation:
                    {feedback.explanation}

                    Final Decision: {final_decision}

                    Write a concise technical justification (max 50 words).

                    Response format:
                    Explanation: <text>
                    """
            out = llm(prompt).strip()
            explanation = (
                out.split("Explanation:")[1].strip()
                if "Explanation:" in out
                else out
            )

        except Exception:
            explanation = f"Final decision derived from verifier status: {feedback.status}"

        decision.cdm_decision = final_decision
        decision.cdm_feedback = explanation
        orch_data.orchestrator_status = "DECIDING"
        return orch_data

    # FALLBACK: FULL LLM DECISION
    try:
        prompt = f"""
                    You are a senior CDM Decision Officer.

                    Verifier Status:
                    {feedback.status}

                    Verifier Explanation:
                    {feedback.explanation}

                    Decide one:
                    ACCEPTED / CORRECTION / INSPECTION / DECLINED

                    Provide short explanation (<=50 words).

                    Response format:
                    Decision: <value>
                    Explanation: <text>
                    """
        out = llm(prompt).strip()

        decision_label = (
            out.split("Decision:")[1].split("\n")[0].strip().upper()
            if "Decision:" in out
            else out.split("\n")[0].strip().upper()
        )

        if "ACCEPT" in decision_label:
            final_decision = "ACCEPTED"
        elif "CORRECT" in decision_label:
            final_decision = "CORRECTION"
        elif "INSPECT" in decision_label:
            final_decision = "INSPECTION"
        elif "DECLINE" in decision_label or "REJECT" in decision_label:
            final_decision = "DECLINED"
        else:
            final_decision = "NEED REVIEW"

        explanation = (
            out.split("Explanation:")[1].strip()
            if "Explanation:" in out
            else out
        )

        decision.cdm_decision = final_decision
        decision.cdm_feedback = explanation

    except Exception as e:
        decision.cdm_decision = "ERROR"
        decision.cdm_feedback = f"Decision failed: {str(e)}"

    orch_data.orchestrator_status = "DECIDING"
    return orch_data
