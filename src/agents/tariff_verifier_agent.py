from typing import Optional

from src.memory.agentstate import (
    TariffExtractedData,
    TariffFeedback,
    CDMDecision,
    OrchestratorAgentState,
    RiskProfile
)
from config import OLLAMA_URL, MODEL_NAME
#from langgraph import agent
from src.utils.client_llm import llm



# Tariff Verifier Agent
#@agent(name="tariff_verifier_agent", description="Verify tariff details using LLM.")
def tariff_verifier_agent(
    orch_data: OrchestratorAgentState,
    risk_profile: RiskProfile
) -> None:
    """
    Verifies tariff details using LLM.
    Reads data from orch_data.cdm_extracted
    Stores result in orch_data.cdm_decisions
    """

    # Extract Required Data
    risk_id = risk_profile.risk_id

    declaration = (
        orch_data.cdm_extracted.declaration_details
        if orch_data.cdm_extracted
        else None
    )

    tariff_data: Optional[TariffExtractedData] = (
        orch_data.cdm_extracted.tariff_extracted_data
        if orch_data.cdm_extracted
        else None
    )

    if not declaration:
        orch_data.cdm_decision.append(
            CDMDecision(
                risk_id=risk_id,
                tariff_feedback=TariffFeedback(
                    status="NEED REVIEW",
                    explanation="Declaration details are missing; tariff verification could not be performed."
                )
            )
        )
        return orch_data

    # If Tariff Data Missing
    if tariff_data is None:
        orch_data.cdm_decision.append(
            CDMDecision(
                risk_id=risk_id,
                tariff_feedback=TariffFeedback(
                    status="INCORRECT HS CODE",
                    explanation="No matching tariff data found for the declared HS code; please revalidate the HS code."
                )
            )
        )
        return orch_data

    # Build Prompt
    prompt = f"""
            You are a customs tariff verification assistant.

            ### USER DECLARATION INPUT
            HS Code: {declaration.hs_code}
            Description: {declaration.goods_description}
            Duty Percentage: {declaration.hs_code_duty_fee}
            Reason: {risk_profile.risk_description}

            ### OFFICIAL TARIFF DATABASE DATA
            HS Code: {tariff_data.hs_code}
            Description: {tariff_data.description}
            Duty Percentage: {tariff_data.duty_percentage}

            ### TASK
            Your verification must follow this strict priority order:

            1. PRIMARY CHECK — Based ONLY on the field mentioned in "Reason"
            2. SECONDARY CHECK — Only if the priority field matches

            ### STATUS RULES
            - Description mismatch → DESCRIPTION MISMATCH
            - Duty mismatch → DUTY PERCENTAGE MISMATCH
            - HS code mismatch → INCORRECT HS CODE
            - If all fields match → ACCEPTED

            ### IMPORTANT
            - First evaluate the field mentioned in "Reason"
            - Stop evaluation immediately if the priority field mismatches
            - Explanation must be under 70 words

            ### RESPONSE FORMAT
            Status: <ACCEPTED / INCORRECT HS CODE / DESCRIPTION MISMATCH / DUTY PERCENTAGE MISMATCH>
            Explanation: <text>
            """

    # Call LLM & Parse Response
    try:
        reply = llm(prompt).strip()

        status = "NEED REVIEW"
        explanation = reply

        if "Status:" in reply:
            status = reply.split("Status:")[1].split("\n")[0].strip()

        if "Explanation:" in reply:
            explanation = reply.split("Explanation:")[1].strip()

        orch_data.cdm_decision = CDMDecision(
                risk_id=risk_id,
                tariff_feedback=TariffFeedback(
                    status=status,
                    explanation=explanation
                )
        )

    except Exception as e:
        orch_data.cdm_decision = CDMDecision(
                risk_id=risk_id,
                tariff_feedback=TariffFeedback(
                    status="NEED REVIEW",
                    explanation="Tariff verification failed due to an internal processing error."
                )
            )
        
    return orch_data
