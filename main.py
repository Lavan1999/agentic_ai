from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from src.memory.agentstate import RiskProfile
from agent_automation import run_orchestrator

app = FastAPI(title="CDM Orchestrator API")

# Pydantic Models for API
class RiskProfileRequest(BaseModel):
    risk_id: str
    risk_type: str
    risk_description: str
    risk_confidence_score: str
    risk_recommended_action: str

class RunCDMRequest(BaseModel):
    declaration_id: str
    risk_profiles: List[RiskProfileRequest]

# API Route
@app.post("/cdm_agent")
def run_cdm_api(request: RunCDMRequest):
    try:
        # Convert RiskProfileRequest → RiskProfile
        risk_profiles = [
            RiskProfile(
                risk_id=r.risk_id,
                risk_type=r.risk_type,
                risk_description=r.risk_description,
                risk_confidence_score=r.risk_confidence_score,
                risk_recommended_action=r.risk_recommended_action
            )
            for r in request.risk_profiles
        ]

        # Run orchestrator
        output = run_orchestrator(
            declaration_id=request.declaration_id,
            risk_profiles=risk_profiles
        )

        return {"status": "success", "result": output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run the API, use the command:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000