from typing import Optional
import requests

from src.memory.agentstate import (
    ValuationExtractedData,
    ValuationFeedback,
    CDMDecision,
    OrchestratorAgentState,
    RiskProfile
)
#from langgraph.prebuilt import agent
from src.utils.client_llm import llm


# Valuation Verifier Agent
#@agent(name="valuation_verifier_agent", description="Verify valuation details using rule-based checks and LLM.")
def valuation_verifier_agent(
    orch_data: OrchestratorAgentState,
    risk_profile: RiskProfile
) -> None:
    """
    Verifies valuation using rule-based checks + LLM explanation.
    Reads from orch_data.cdm_extracted
    Assigns CDMDecision into orch_data.cdm_decision
    """

    risk_id = risk_profile.risk_id

    # Extract Required Data
    cdm_extracted = orch_data.cdm_extracted

    declaration = (
        cdm_extracted.declaration_details
        if cdm_extracted
        else None
    )

    valuation_data: Optional[ValuationExtractedData] = (
        cdm_extracted.valuation_extracted_data
        if cdm_extracted
        else None
    )

    # Validation
    if not declaration:
        orch_data.cdm_decision = CDMDecision(
            risk_id=risk_id,
            valuation_feedback=ValuationFeedback(
                status="NEED REVIEW",
                explanation="Declaration details are missing; valuation verification could not be performed."
            )
        )
        return

    if valuation_data is None:
        orch_data.cdm_decision = CDMDecision(
            risk_id=risk_id,
            valuation_feedback=ValuationFeedback(
                status="INVALID HS CODE",
                explanation="No valuation reference data found for the declared HS code; please revalidate."
            )
        )
        return

    # Prepare Numeric Values
    try:
        declared_price = float(declaration.goods_value or 0)
        quantity = float(declaration.static_quantity_unit or 1)

        db_unit_price = float(valuation_data.price or 0)
        allowed_variation = float(valuation_data.variation_percentage or 0)
    except ValueError:
        orch_data.cdm_decision = CDMDecision(
            risk_id=risk_id,
            valuation_feedback=ValuationFeedback(
                status="NEED REVIEW",
                explanation="Invalid numeric values encountered during valuation verification."
            )
        )
        return

    db_total_price = db_unit_price * quantity

    lower_limit = db_total_price * (1 - allowed_variation / 100)
    upper_limit = db_total_price * (1 + allowed_variation / 100)

    # Deterministic Decision
    if declared_price < lower_limit:
        status = "UNDER VALUED"
    elif declared_price > upper_limit:
        status = "OVER VALUED"
    else:
        status = "ACCEPTED"

    # Build LLM Prompt
    prompt = f"""
            You are a customs valuation verification specialist.

            ### USER DECLARATION INPUT
            HS Code: {declaration.hs_code}
            Quantity: {quantity}
            Declared Total Price: {declared_price}

            ### DATABASE REFERENCE VALUES
            Unit Price: {db_unit_price}
            Allowed Variation: ±{allowed_variation}%
            DB Total Price: {db_total_price}
            Acceptable Range: {lower_limit:.2f} - {upper_limit:.2f}

            ### RISK PROFILE REASON
            Reason: {risk_profile.risk_description}

            ### RESULT (ALREADY DETERMINED)
            Status: {status}

            ### TASK
            Write a concise technical explanation (<50 words) justifying the above status.
            Do NOT re-calculate values.
            Do NOT change the status.

            ### RESPONSE FORMAT
            Status: {status}
            Explanation: <text>
            """

    # Call LLM & Store Decision
    try:
        reply = llm(prompt).strip()

        explanation = reply
        if "Explanation:" in reply:
            explanation = reply.split("Explanation:")[1].strip()

        orch_data.cdm_decision = CDMDecision(
            risk_id=risk_id,
            valuation_feedback=ValuationFeedback(
                status=status,
                explanation=explanation
            )
        )

    except Exception:
        orch_data.cdm_decision = CDMDecision(
            risk_id=risk_id,
            valuation_feedback=ValuationFeedback(
                status=status,
                explanation="Valuation status determined by rule-based checks; LLM explanation unavailable."
            )
        )
