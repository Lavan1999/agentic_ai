import requests
from typing import Optional
from src.memory.agentstate import DeclarationDetails
from config import GRAPHQL_URL
#from langchain.tools import tool


#@tool(description="Fetch declaration details from the database using the declaration ID")
def fetch_declaration_details(declaration_id: str) -> Optional[DeclarationDetails]:

    headers = {
        "Content-Type": "application/json"
    }

    query = """
    query ($declaration_id: String!) {
      declaration_versioned_list(declaration_id: $declaration_id) {
        versioned_data
      }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "declaration_id": declaration_id
        }
    }

    try:
        response = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"\n---> Declaration API request failed: {e}")
        return None

    data = response.json()

    # Defensive Checks
    if not data.get("data"):
        print(f"\n---> No data returned for declaration ID: {declaration_id}")
        return None

    versioned_list = data["data"].get("declaration_versioned_list")

    if not versioned_list:
        print(f"\n---> No declaration versions found for declaration ID: {declaration_id}")
        return None

    if not isinstance(versioned_list, list) or len(versioned_list) == 0:
        print(f"\n---> Empty declaration version list for declaration ID: {declaration_id}")
        return None

    versioned_data = versioned_list[0].get("versioned_data")

    if not versioned_data:
        print(f"\n---> No versioned data found for declaration ID: {declaration_id}")
        return None

    # Extract Nested Data Safely
    items = versioned_data.get("items_data") or []
    invoices = versioned_data.get("invoice_datas") or []
    payments = versioned_data.get("payment_datas") or []

    if not items:
        print(f"\n---> No item data found for declaration ID: {declaration_id}")
        return None

    item = items[0]
    invoice = invoices[0] if invoices else {}
    payment = payments[0] if payments else {}

    return DeclarationDetails(
        hs_code=item.get("hsCode"),
        goods_value=item.get("goods_value"),
        goods_description=item.get("goods_description"),
        hs_code_duty_fee=item.get("hs_code_duty_fee"),
        static_quantity_unit=item.get("static_quantity_unit"),
        currency=invoice.get("currency"),
        deposit=payment.get("deposit")
    )




# import requests
# from src.memory.agentstate import DeclarationDetails


# def fetch_declaration_details(declaration_id: str) -> DeclarationDetails:
#     url = "https://declaration.dubaicustoms.network/graphql/"

#     headers = {
#         "Content-Type": "application/json"
#     }

#     query = """
#     query ($declaration_id: String!) {
#       declaration_versioned_list(declaration_id: $declaration_id) {
#         versioned_data
#       }
#     }
#     """

#     payload = {
#         "query": query,
#         "variables": {
#             "declaration_id": declaration_id
#         }
#     }

#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()

#     data = response.json()

#     versioned_data = data["data"]["declaration_versioned_list"][0]["versioned_data"]

#     # Extract JSON manually
#     item = versioned_data["items_data"][0]
#     invoice = versioned_data["invoice_datas"][0]
#     payment = versioned_data["payment_datas"][0]

#     return DeclarationDetails(
#         hs_code=item.get("hsCode"),
#         goods_value=item.get("goods_value"),
#         goods_description=item.get("goods_description"),
#         hs_code_duty_fee=item.get("hs_code_duty_fee"),
#         static_quantity_unit=item.get("static_quantity_unit"),
#         currency=invoice.get("currency"),
#         deposit=payment.get("deposit")
#     )


# ====================
