import requests
from typing import Optional

# import your models
from src.memory.agentstate import (
    OrchestratorAgentState,
    CDMExtracted,
    TariffExtractedData,
    ValuationExtractedData
)
from config import TARIFF_URL

# TARIFF API FUNCTION
def fetch_tariff_data(
    hs_code: str,
    agent_state: OrchestratorAgentState
) -> OrchestratorAgentState:

    params = {"search_param": hs_code}
    headers = {
        "Authorization": "Bearer tariff_auth_1234567890abcdef"
    }

    response = requests.get(TARIFF_URL, headers=headers, params=params)

    if response.status_code != 200:
        return agent_state  # silently skip

    data = response.json()

    results = data.get("results", [])
    if not results:
        return agent_state

    tariff = results[0]

    tariff_extracted = TariffExtractedData(
        hs_code=tariff.get("hs_code"),
        description=tariff.get("description"),
        duty_percentage=tariff.get("duty_fee"),
    )

    if agent_state.cdm_extracted is None:
        agent_state.cdm_extracted = CDMExtracted()

    agent_state.cdm_extracted.tariff_extracted_data = tariff_extracted

    return agent_state


# VALUATION API FUNCTION
def fetch_valuation_data(
    hs_code: str,
    agent_state: OrchestratorAgentState
) -> OrchestratorAgentState:

    url = f"https://valuation.finloge.com/api/products/hs-code/{hs_code}/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer a93dfb27c6e81f42"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return agent_state

    data = response.json()

    products = data.get("data", [])
    if not products:
        return agent_state

    product = products[0]
    prices = product.get("prices", [])
    price_obj = prices[0] if prices else {}

    valuation_extracted = ValuationExtractedData(
        product_id=product.get("product_id"),
        description=product.get("description"),
        variation_percentage=product.get("variation_percentage"),
        unit_name=product.get("unit_name"),
        price=price_obj.get("price"),
        currency=price_obj.get("currency"),
    )

    if agent_state.cdm_extracted is None:
        agent_state.cdm_extracted = CDMExtracted()

    agent_state.cdm_extracted.valuation_extracted_data = valuation_extracted

    return agent_state
