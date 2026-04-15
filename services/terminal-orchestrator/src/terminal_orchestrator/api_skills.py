from fastapi import APIRouter, Depends, Request

from .auth import verify_bearer

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("", dependencies=[Depends(verify_bearer)])
@router.get("/", dependencies=[Depends(verify_bearer)])
async def list_skills(request: Request) -> dict:
    manager = request.app.state.manager
    mount = request.app.state.settings.skills_mount
    return {
        "mount": mount,
        "skills": manager.skills_manifest,
    }
