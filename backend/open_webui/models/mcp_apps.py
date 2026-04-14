import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context
from open_webui.models.users import Users, UserResponse
from open_webui.models.groups import Groups
from open_webui.models.access_grants import AccessGrantModel, AccessGrants

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, BigInteger, Boolean, Column, String, Text, or_

log = logging.getLogger(__name__)

####################
# McpApp DB Schema
####################


class McpApp(Base):
    __tablename__ = 'mcp_app'

    id = Column(String, primary_key=True, unique=True)
    user_id = Column(String)
    name = Column(Text, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # MCP Connection
    transport = Column(String)  # http_streamable, sse, stdio
    url = Column(Text, nullable=True)  # for http_streamable and sse
    command = Column(Text, nullable=True)  # for stdio
    args = Column(JSON, nullable=True)  # for stdio args array
    env_encrypted = Column(Text, nullable=True)  # encrypted JSON dict for stdio env vars
    auth_type = Column(String, nullable=True)  # bearer, oauth_2.1, session, none
    auth_config_encrypted = Column(Text, nullable=True)  # encrypted JSON auth credentials

    # App Configuration
    tool_configs = Column(JSON, nullable=True)  # array of per-tool config objects
    skill_prompt = Column(Text, nullable=True)  # admin-written behavioral instructions
    widget_ids = Column(JSON, nullable=True)  # array of linked widget IDs

    # Access & Meta
    access_control = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


####################
# Pydantic Models
####################


class McpAppToolConfig(BaseModel):
    name: str
    enabled: bool = True
    requires_confirmation: bool = False
    confirmation_widget_id: Optional[str] = None
    display_name: Optional[str] = None


class McpAppMeta(BaseModel):
    tags: Optional[list[str]] = []


class McpAppModel(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

    transport: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env_encrypted: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config_encrypted: Optional[str] = None

    tool_configs: Optional[list[dict]] = None
    skill_prompt: Optional[str] = None
    widget_ids: Optional[list[str]] = None

    access_control: Optional[dict] = None
    meta: Optional[McpAppMeta] = None
    access_grants: list[AccessGrantModel] = Field(default_factory=list)

    updated_at: int
    created_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class McpAppForm(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

    transport: str  # http_streamable, sse, stdio
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict] = None  # plaintext env vars (encrypted before storage)
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None  # plaintext auth config (encrypted before storage)

    tool_configs: Optional[list[dict]] = None
    skill_prompt: Optional[str] = None
    widget_ids: Optional[list[str]] = None

    access_control: Optional[dict] = None
    meta: McpAppMeta = McpAppMeta()
    access_grants: Optional[list[dict]] = None


class McpAppResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

    transport: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    auth_type: Optional[str] = None

    # Sensitive fields are redacted — only flags
    has_env: bool = False
    has_auth_config: bool = False

    tool_configs: Optional[list[dict]] = None
    skill_prompt: Optional[str] = None
    widget_ids: Optional[list[str]] = None

    access_control: Optional[dict] = None
    meta: Optional[McpAppMeta] = None
    access_grants: list[AccessGrantModel] = Field(default_factory=list)

    updated_at: int
    created_at: int


class McpAppUserResponse(McpAppResponse):
    user: Optional[UserResponse] = None

    model_config = ConfigDict(extra='allow')


class McpAppListResponse(BaseModel):
    items: list[McpAppUserResponse] = []
    total: int = 0


####################
# Table Operations
####################


class McpAppsTable:
    def _get_access_grants(self, app_id: str, db: Optional[Session] = None) -> list[AccessGrantModel]:
        return AccessGrants.get_grants_by_resource('mcp_app', app_id, db=db)

    def _to_model(
        self,
        app: McpApp,
        access_grants: Optional[list[AccessGrantModel]] = None,
        db: Optional[Session] = None,
    ) -> McpAppModel:
        app_data = McpAppModel.model_validate(app).model_dump(exclude={'access_grants'})
        app_data['access_grants'] = (
            access_grants if access_grants is not None else self._get_access_grants(app_data['id'], db=db)
        )
        return McpAppModel.model_validate(app_data)

    def _to_response(self, model: McpAppModel) -> McpAppResponse:
        data = model.model_dump(exclude={'env_encrypted', 'auth_config_encrypted'})
        data['has_env'] = bool(model.env_encrypted)
        data['has_auth_config'] = bool(model.auth_config_encrypted)
        return McpAppResponse.model_validate(data)

    def insert_new_mcp_app(
        self,
        user_id: str,
        form_data: McpAppForm,
        env_encrypted: Optional[str] = None,
        auth_config_encrypted: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[McpAppModel]:
        with get_db_context(db) as db:
            try:
                app_id = str(uuid.uuid4())
                now = int(time.time())

                result = McpApp(
                    id=app_id,
                    user_id=user_id,
                    name=form_data.name,
                    description=form_data.description,
                    icon=form_data.icon,
                    is_active=form_data.is_active,
                    transport=form_data.transport,
                    url=form_data.url,
                    command=form_data.command,
                    args=form_data.args,
                    env_encrypted=env_encrypted,
                    auth_type=form_data.auth_type,
                    auth_config_encrypted=auth_config_encrypted,
                    tool_configs=form_data.tool_configs,
                    skill_prompt=form_data.skill_prompt,
                    widget_ids=form_data.widget_ids,
                    access_control=form_data.access_control,
                    meta=form_data.meta.model_dump() if form_data.meta else None,
                    updated_at=now,
                    created_at=now,
                )
                db.add(result)
                db.commit()
                db.refresh(result)

                if form_data.access_grants:
                    AccessGrants.set_access_grants('mcp_app', result.id, form_data.access_grants, db=db)

                return self._to_model(result, db=db)
            except Exception as e:
                log.exception(f'Error creating MCP App: {e}')
                return None

    def get_mcp_app_by_id(self, id: str, db: Optional[Session] = None) -> Optional[McpAppModel]:
        try:
            with get_db_context(db) as db:
                app = db.get(McpApp, id)
                return self._to_model(app, db=db) if app else None
        except Exception:
            return None

    def get_mcp_apps(self, db: Optional[Session] = None) -> list[McpAppUserResponse]:
        with get_db_context(db) as db:
            all_apps = db.query(McpApp).order_by(McpApp.updated_at.desc()).all()

            user_ids = list(set(app.user_id for app in all_apps))
            app_ids = [app.id for app in all_apps]

            users = Users.get_users_by_user_ids(user_ids, db=db) if user_ids else []
            users_dict = {user.id: user for user in users}
            grants_map = AccessGrants.get_grants_by_resources('mcp_app', app_ids, db=db)

            apps = []
            for app in all_apps:
                user = users_dict.get(app.user_id)
                model = self._to_model(
                    app,
                    access_grants=grants_map.get(app.id, []),
                    db=db,
                )
                response = self._to_response(model)
                apps.append(
                    McpAppUserResponse.model_validate(
                        {
                            **response.model_dump(),
                            'user': user.model_dump() if user else None,
                        }
                    )
                )
            return apps

    def get_mcp_apps_by_user_id(
        self, user_id: str, permission: str = 'read', db: Optional[Session] = None
    ) -> list[McpAppUserResponse]:
        apps = self.get_mcp_apps(db=db)
        user_group_ids = {group.id for group in Groups.get_groups_by_member_id(user_id, db=db)}

        return [
            app
            for app in apps
            if app.user_id == user_id
            or AccessGrants.has_access(
                user_id=user_id,
                resource_type='mcp_app',
                resource_id=app.id,
                permission=permission,
                user_group_ids=user_group_ids,
                db=db,
            )
        ]

    def update_mcp_app_by_id(
        self,
        id: str,
        updated: dict,
        env_encrypted: Optional[str] = None,
        auth_config_encrypted: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[McpAppModel]:
        try:
            with get_db_context(db) as db:
                access_grants = updated.pop('access_grants', None)
                # Remove plaintext sensitive fields — they should not be stored
                updated.pop('env', None)
                updated.pop('auth_config', None)

                update_data = {**updated, 'updated_at': int(time.time())}
                if env_encrypted is not None:
                    update_data['env_encrypted'] = env_encrypted
                if auth_config_encrypted is not None:
                    update_data['auth_config_encrypted'] = auth_config_encrypted

                db.query(McpApp).filter_by(id=id).update(update_data)
                db.commit()

                if access_grants is not None:
                    AccessGrants.set_access_grants('mcp_app', id, access_grants, db=db)

                app = db.query(McpApp).get(id)
                db.refresh(app)
                return self._to_model(app, db=db)
        except Exception:
            return None

    def toggle_mcp_app_by_id(self, id: str, db: Optional[Session] = None) -> Optional[McpAppModel]:
        with get_db_context(db) as db:
            try:
                app = db.query(McpApp).filter_by(id=id).first()
                if not app:
                    return None

                app.is_active = not app.is_active
                app.updated_at = int(time.time())
                db.commit()
                db.refresh(app)

                return self._to_model(app, db=db)
            except Exception:
                return None

    def delete_mcp_app_by_id(self, id: str, db: Optional[Session] = None) -> bool:
        try:
            with get_db_context(db) as db:
                AccessGrants.revoke_all_access('mcp_app', id, db=db)
                db.query(McpApp).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False


McpApps = McpAppsTable()
