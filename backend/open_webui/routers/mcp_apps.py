import logging
from typing import Optional

from open_webui.models.groups import Groups
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from open_webui.internal.db import get_session
from open_webui.models.mcp_apps import (
    McpAppForm,
    McpAppModel,
    McpAppResponse,
    McpAppUserResponse,
    McpAppListResponse,
    McpApps,
)
from open_webui.models.access_grants import AccessGrants
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_permission, filter_allowed_access_grants
from open_webui.utils.oauth import encrypt_data, decrypt_data

from open_webui.config import BYPASS_ADMIN_ACCESS_CONTROL
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENABLE_MCP_STDIO

log = logging.getLogger(__name__)

router = APIRouter()


def _unwrap_exception(e: Exception) -> str:
    """Extract a human-readable message from an exception, unwrapping ExceptionGroups."""
    if isinstance(e, ExceptionGroup):
        messages = []
        for sub in e.exceptions:
            messages.append(_unwrap_exception(sub))
        return '; '.join(messages)
    return str(e)


############################
# GetMcpApps
############################


@router.get('/', response_model=list[McpAppUserResponse])
async def get_mcp_apps(
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL:
        apps = McpApps.get_mcp_apps(db=db)
    else:
        apps = McpApps.get_mcp_apps_by_user_id(user.id, 'read', db=db)

    # Filter to only active apps for non-admin users
    if user.role != 'admin':
        apps = [app for app in apps if app.is_active]

    return apps


############################
# CreateMcpApp
############################


@router.post('/create', response_model=Optional[McpAppResponse])
async def create_mcp_app(
    request: Request,
    form_data: McpAppForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    # Validate transport
    if form_data.transport not in ('http_streamable', 'sse', 'stdio'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('Invalid transport type. Must be http_streamable, sse, or stdio.'),
        )

    if form_data.transport == 'stdio' and not ENABLE_MCP_STDIO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(
                'stdio transport is disabled. Set ENABLE_MCP_STDIO=true to enable.'
            ),
        )

    # Encrypt sensitive fields
    env_encrypted = None
    if form_data.env:
        env_encrypted = encrypt_data(form_data.env)

    auth_config_encrypted = None
    if form_data.auth_config:
        auth_config_encrypted = encrypt_data(form_data.auth_config)

    try:
        app = McpApps.insert_new_mcp_app(
            user.id,
            form_data,
            env_encrypted=env_encrypted,
            auth_config_encrypted=auth_config_encrypted,
            db=db,
        )
        if app:
            return McpApps._to_response(app)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT('Error creating MCP App'),
            )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f'Failed to create MCP App: {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(str(e)),
        )


############################
# GetMcpAppById
############################


@router.get('/id/{id}', response_model=Optional[McpAppResponse])
async def get_mcp_app_by_id(
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)

    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        user.role == 'admin'
        or app.user_id == user.id
        or AccessGrants.has_access(
            user_id=user.id,
            resource_type='mcp_app',
            resource_id=app.id,
            permission='read',
            db=db,
        )
    ):
        return McpApps._to_response(app)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )


############################
# UpdateMcpAppById
############################


@router.post('/id/{id}/update', response_model=Optional[McpAppResponse])
async def update_mcp_app_by_id(
    request: Request,
    id: str,
    form_data: McpAppForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if app.user_id != user.id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if form_data.transport == 'stdio' and not ENABLE_MCP_STDIO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(
                'stdio transport is disabled. Set ENABLE_MCP_STDIO=true to enable.'
            ),
        )

    # Encrypt sensitive fields if provided
    env_encrypted = None
    if form_data.env:
        env_encrypted = encrypt_data(form_data.env)

    auth_config_encrypted = None
    if form_data.auth_config:
        auth_config_encrypted = encrypt_data(form_data.auth_config)

    try:
        updated = form_data.model_dump(exclude={'env', 'auth_config'})
        result = McpApps.update_mcp_app_by_id(
            id,
            updated,
            env_encrypted=env_encrypted,
            auth_config_encrypted=auth_config_encrypted,
            db=db,
        )

        if result:
            return McpApps._to_response(result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT('Error updating MCP App'),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(str(e)),
        )


############################
# UpdateMcpAppAccessById
############################


class McpAppAccessGrantsForm(BaseModel):
    access_grants: list[dict]


@router.post('/id/{id}/access/update', response_model=Optional[McpAppResponse])
async def update_mcp_app_access_by_id(
    request: Request,
    id: str,
    form_data: McpAppAccessGrantsForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if app.user_id != user.id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    form_data.access_grants = filter_allowed_access_grants(
        request.app.state.config.USER_PERMISSIONS,
        user.id,
        user.role,
        form_data.access_grants,
        'sharing.public_mcp_apps',
    )

    AccessGrants.set_access_grants('mcp_app', id, form_data.access_grants, db=db)

    app = McpApps.get_mcp_app_by_id(id, db=db)
    return McpApps._to_response(app) if app else None


############################
# ToggleMcpAppById
############################


@router.post('/id/{id}/toggle', response_model=Optional[McpAppResponse])
async def toggle_mcp_app_by_id(
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if user.role != 'admin' and app.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = McpApps.toggle_mcp_app_by_id(id, db=db)
    if result:
        return McpApps._to_response(result)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('Error toggling MCP App'),
        )


############################
# DeleteMcpAppById
############################


@router.delete('/id/{id}/delete', response_model=bool)
async def delete_mcp_app_by_id(
    request: Request,
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if app.user_id != user.id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    return McpApps.delete_mcp_app_by_id(id, db=db)


############################
# TestMcpAppConnection
############################


@router.post('/id/{id}/test')
async def test_mcp_app_connection(
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if user.role != 'admin' and app.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if app.transport == 'stdio' and not ENABLE_MCP_STDIO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('stdio transport is disabled.'),
        )

    try:
        from open_webui.utils.mcp.client import MCPClient

        client = MCPClient()

        # Build connection params based on transport
        if app.transport in ('http_streamable', 'sse'):
            headers = {}
            if app.auth_type == 'bearer' and app.auth_config_encrypted:
                auth_config = decrypt_data(app.auth_config_encrypted)
                headers['Authorization'] = f'Bearer {auth_config.get("key", "")}'

            await client.connect(
                url=app.url,
                headers=headers,
                transport=app.transport,
            )
        elif app.transport == 'stdio':
            env = {}
            if app.env_encrypted:
                env = decrypt_data(app.env_encrypted)

            await client.connect(
                transport='stdio',
                command=app.command,
                args=app.args or [],
                env=env,
            )

        tool_specs = await client.list_tool_specs()
        await client.disconnect()

        return {
            'status': True,
            'tools': tool_specs,
            'tool_count': len(tool_specs),
        }
    except Exception as e:
        log.exception(f'MCP App connection test failed: {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(f'Connection failed: {_unwrap_exception(e)}'),
        )


############################
# TestMcpAppConnectionDirect
# (test before saving — uses form data directly)
############################


class McpAppTestForm(BaseModel):
    transport: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None


@router.post('/test')
async def test_mcp_app_connection_direct(
    form_data: McpAppTestForm,
    user=Depends(get_verified_user),
):
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if form_data.transport == 'stdio' and not ENABLE_MCP_STDIO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('stdio transport is disabled.'),
        )

    try:
        from open_webui.utils.mcp.client import MCPClient

        client = MCPClient()

        if form_data.transport in ('http_streamable', 'sse'):
            headers = {}
            if form_data.auth_type == 'bearer' and form_data.auth_config:
                headers['Authorization'] = f'Bearer {form_data.auth_config.get("key", "")}'

            await client.connect(
                url=form_data.url,
                headers=headers,
                transport=form_data.transport,
            )
        elif form_data.transport == 'stdio':
            await client.connect(
                transport='stdio',
                command=form_data.command,
                args=form_data.args or [],
                env=form_data.env or {},
            )

        tool_specs = await client.list_tool_specs()
        await client.disconnect()

        return {
            'status': True,
            'tools': tool_specs,
            'tool_count': len(tool_specs),
        }
    except Exception as e:
        log.exception(f'MCP connection test failed: {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(f'Connection failed: {_unwrap_exception(e)}'),
        )


############################
# CallMcpAppTool
# (direct tool invocation for mcp-ui iframe `tool` actions)
############################


class McpAppToolCallForm(BaseModel):
    params: Optional[dict] = None
    confirmed: Optional[bool] = False


@router.post('/id/{id}/tools/{tool_name}/call')
async def call_mcp_app_tool(
    request: Request,
    id: str,
    tool_name: str,
    form_data: McpAppToolCallForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    app = McpApps.get_mcp_app_by_id(id, db=db)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Access control: admin, owner, or has read grant on this app.
    if not (
        user.role == 'admin'
        or app.user_id == user.id
        or AccessGrants.has_access(
            user_id=user.id,
            resource_type='mcp_app',
            resource_id=app.id,
            permission='read',
            db=db,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    if not app.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('MCP App is disabled.'),
        )

    if app.transport == 'stdio' and not ENABLE_MCP_STDIO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT('stdio transport is disabled.'),
        )

    # Enforce per-tool config: enabled + requires_confirmation.
    tool_cfg = {}
    for tc in (app.tool_configs or []):
        name = tc.get('name') or tc.get('tool_name', '')
        if name == tool_name:
            tool_cfg = tc
            break

    if tool_cfg.get('enabled', True) is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.DEFAULT(f'Tool "{tool_name}" is disabled on this MCP App.'),
        )

    if tool_cfg.get('requires_confirmation', False) and not form_data.confirmed:
        return {
            'requires_confirmation': True,
            'tool_name': tool_name,
            'display_name': tool_cfg.get('display_name') or tool_name,
            'confirmation_widget_id': tool_cfg.get('confirmation_widget_id'),
            'params': form_data.params or {},
        }

    from open_webui.utils.mcp.client import MCPClient
    from open_webui.utils.mcp.process_manager import mcp_process_registry

    client = None
    owns_client = False

    try:
        if app.transport == 'stdio':
            entry = mcp_process_registry.get(user.id, app.id)
            if entry:
                client = entry.client
            else:
                env = {}
                if app.env_encrypted:
                    env = decrypt_data(app.env_encrypted)
                entry = await mcp_process_registry.spawn(
                    user_id=user.id,
                    app_id=app.id,
                    command=app.command or '',
                    args=app.args or [],
                    env=env,
                )
                client = entry.client
        else:
            headers = {}
            if app.auth_type == 'bearer' and app.auth_config_encrypted:
                auth_config = decrypt_data(app.auth_config_encrypted)
                headers['Authorization'] = f'Bearer {auth_config.get("key", "")}'
            elif app.auth_type == 'session' and getattr(request.state, 'token', None):
                headers['Authorization'] = f'Bearer {request.state.token.credentials}'

            client = MCPClient()
            owns_client = True
            await client.connect(
                url=app.url,
                headers=headers if headers else None,
                transport=app.transport,
            )

        result = await client.call_tool_with_meta(tool_name, form_data.params or {})
        content = result.get('content')
        meta = result.get('meta') or {}

        ui_resource = None
        ui_meta = (meta.get('ui') or {}) if isinstance(meta, dict) else {}
        resource_uri = ui_meta.get('resourceUri') if isinstance(ui_meta, dict) else None
        if resource_uri:
            try:
                read_result = await client.read_resource(resource_uri)
                contents = (read_result or {}).get('contents') or []
                first = contents[0] if contents else None
                if first:
                    ui_resource = {
                        'uri': first.get('uri') or resource_uri,
                        'mimeType': first.get('mimeType'),
                    }
                    if first.get('text') is not None:
                        ui_resource['text'] = first.get('text')
                    if first.get('blob') is not None:
                        ui_resource['blob'] = first.get('blob')
            except Exception as ui_err:
                log.warning(
                    f'MCP UI resource read failed for {tool_name} ({resource_uri}): {ui_err}'
                )

        return {
            'content': content,
            'ui_resource': ui_resource,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f'MCP tool call failed ({app.id}/{tool_name}): {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(f'Tool call failed: {_unwrap_exception(e)}'),
        )
    finally:
        if owns_client and client is not None:
            try:
                await client.disconnect()
            except Exception:
                pass
