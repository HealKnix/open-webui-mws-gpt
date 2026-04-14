from fastapi import APIRouter, Depends, HTTPException, Request

from .auth import verify_bearer
from .policies import Policy

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


@router.get("", dependencies=[Depends(verify_bearer)])
@router.get("/", dependencies=[Depends(verify_bearer)])
async def list_policies(request: Request) -> dict:
    registry = request.app.state.policies
    return {"policies": [policy.model_dump() for policy in registry.all()]}


@router.get("/{policy_id}", dependencies=[Depends(verify_bearer)])
async def get_policy(policy_id: str, request: Request) -> dict:
    registry = request.app.state.policies
    policy = registry.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.model_dump()


@router.put("/{policy_id}", dependencies=[Depends(verify_bearer)])
async def put_policy(policy_id: str, payload: dict, request: Request) -> dict:
    data = dict(payload)
    data["id"] = policy_id
    try:
        policy = Policy.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid policy: {exc}") from exc
    registry = request.app.state.policies
    stored = registry.upsert(policy)
    return stored.model_dump()
