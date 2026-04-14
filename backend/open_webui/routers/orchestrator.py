from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from open_webui.orchestration.executor import build_execution_result
from open_webui.orchestration.planner import build_plan
from open_webui.orchestration.registry import MTS_ROUTER_MODEL_ID, build_registry
from open_webui.orchestration.schema import PolicyMode
from open_webui.utils.auth import get_admin_user
from open_webui.utils.models import get_all_models


router = APIRouter()


class OrchestratorConfigForm(BaseModel):
    default_policy_mode: PolicyMode


class OrchestratorExecuteForm(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    policy_mode: PolicyMode = 'balanced'
    dry_run: bool = False


def _build_form_payload(form_data: OrchestratorExecuteForm) -> dict[str, Any]:
    metadata = {
        **form_data.metadata,
        'files': form_data.files,
    }

    return {
        'model': MTS_ROUTER_MODEL_ID,
        'messages': form_data.messages,
        'metadata': metadata,
    }


@router.get('/config')
async def get_orchestrator_config(request: Request, user=Depends(get_admin_user)):
    return {
        'enabled': True,
        'default_policy_mode': getattr(request.app.state, 'MTS_ROUTER_DEFAULT_POLICY_MODE', 'balanced'),
        'supported_policy_modes': ['fast', 'balanced', 'quality'],
        'model_id': MTS_ROUTER_MODEL_ID,
    }


@router.post('/config/update')
async def update_orchestrator_config(
    request: Request,
    form_data: OrchestratorConfigForm,
    user=Depends(get_admin_user),
):
    request.app.state.MTS_ROUTER_DEFAULT_POLICY_MODE = form_data.default_policy_mode
    return {
        'enabled': True,
        'default_policy_mode': request.app.state.MTS_ROUTER_DEFAULT_POLICY_MODE,
        'supported_policy_modes': ['fast', 'balanced', 'quality'],
        'model_id': MTS_ROUTER_MODEL_ID,
    }


@router.get('/registry')
async def get_registry(request: Request, user=Depends(get_admin_user)):
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)
    registry = build_registry(request)
    return {
        'provider': registry.get('provider'),
        'models': [
            {
                'id': model['id'],
                'name': model.get('name', model['id']),
                'capabilities': model.get('capabilities', {}),
            }
            for model in registry.get('models', [])
        ],
    }


@router.post('/plan')
async def plan(request: Request, form_data: OrchestratorExecuteForm, user=Depends(get_admin_user)):
    payload = _build_form_payload(form_data)
    plan = build_plan(payload, policy_mode=form_data.policy_mode)
    return plan.model_dump()


@router.post('/execute')
async def execute(request: Request, form_data: OrchestratorExecuteForm, user=Depends(get_admin_user)):
    payload = _build_form_payload(form_data)
    try:
        result = await build_execution_result(
            request=request,
            form_data=payload,
            user=user,
            policy_mode=form_data.policy_mode,
            dry_run=form_data.dry_run,
        )
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
