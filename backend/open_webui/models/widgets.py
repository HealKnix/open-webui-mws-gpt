import logging
import time
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
# Widgets DB Schema
####################


class Widget(Base):
    __tablename__ = 'widget'

    id = Column(String, primary_key=True, unique=True)
    user_id = Column(String)
    name = Column(Text, unique=True)
    description = Column(Text, nullable=True)
    content = Column(Text)
    meta = Column(JSON)
    is_active = Column(Boolean, default=True)

    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class WidgetMeta(BaseModel):
    tags: Optional[list[str]] = []


class WidgetModel(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    content: str
    meta: WidgetMeta
    is_active: bool = True
    access_grants: list[AccessGrantModel] = Field(default_factory=list)

    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class WidgetUserModel(WidgetModel):
    user: Optional[UserResponse] = None


class WidgetResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    meta: WidgetMeta
    is_active: bool = True
    access_grants: list[AccessGrantModel] = Field(default_factory=list)
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class WidgetUserResponse(WidgetResponse):
    user: Optional[UserResponse] = None

    model_config = ConfigDict(extra='allow')


class WidgetAccessResponse(WidgetUserResponse):
    write_access: Optional[bool] = False


class WidgetForm(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content: str
    meta: WidgetMeta = WidgetMeta()
    is_active: bool = True
    access_grants: Optional[list[dict]] = None


class WidgetListResponse(BaseModel):
    items: list[WidgetUserResponse] = []
    total: int = 0


class WidgetAccessListResponse(BaseModel):
    items: list[WidgetAccessResponse] = []
    total: int = 0


class WidgetsTable:
    def _get_access_grants(self, widget_id: str, db: Optional[Session] = None) -> list[AccessGrantModel]:
        return AccessGrants.get_grants_by_resource('widget', widget_id, db=db)

    def _to_widget_model(
        self,
        widget: Widget,
        access_grants: Optional[list[AccessGrantModel]] = None,
        db: Optional[Session] = None,
    ) -> WidgetModel:
        widget_data = WidgetModel.model_validate(widget).model_dump(exclude={'access_grants'})
        widget_data['access_grants'] = (
            access_grants if access_grants is not None else self._get_access_grants(widget_data['id'], db=db)
        )
        return WidgetModel.model_validate(widget_data)

    def insert_new_widget(
        self,
        user_id: str,
        form_data: WidgetForm,
        db: Optional[Session] = None,
    ) -> Optional[WidgetModel]:
        with get_db_context(db) as db:
            try:
                result = Widget(
                    **{
                        **form_data.model_dump(exclude={'access_grants'}),
                        'user_id': user_id,
                        'updated_at': int(time.time()),
                        'created_at': int(time.time()),
                    }
                )
                db.add(result)
                db.commit()
                db.refresh(result)
                AccessGrants.set_access_grants('widget', result.id, form_data.access_grants, db=db)
                if result:
                    return self._to_widget_model(result, db=db)
                else:
                    return None
            except Exception as e:
                log.exception(f'Error creating a new widget: {e}')
                return None

    def get_widget_by_id(self, id: str, db: Optional[Session] = None) -> Optional[WidgetModel]:
        try:
            with get_db_context(db) as db:
                widget = db.get(Widget, id)
                return self._to_widget_model(widget, db=db) if widget else None
        except Exception:
            return None

    def get_widget_by_name(self, name: str, db: Optional[Session] = None) -> Optional[WidgetModel]:
        try:
            with get_db_context(db) as db:
                widget = db.query(Widget).filter_by(name=name).first()
                return self._to_widget_model(widget, db=db) if widget else None
        except Exception:
            return None

    def get_widgets(self, db: Optional[Session] = None) -> list[WidgetUserModel]:
        with get_db_context(db) as db:
            all_widgets = db.query(Widget).order_by(Widget.updated_at.desc()).all()

            user_ids = list(set(widget.user_id for widget in all_widgets))
            widget_ids = [widget.id for widget in all_widgets]

            users = Users.get_users_by_user_ids(user_ids, db=db) if user_ids else []
            users_dict = {user.id: user for user in users}
            grants_map = AccessGrants.get_grants_by_resources('widget', widget_ids, db=db)

            widgets = []
            for widget in all_widgets:
                user = users_dict.get(widget.user_id)
                widgets.append(
                    WidgetUserModel.model_validate(
                        {
                            **self._to_widget_model(
                                widget,
                                access_grants=grants_map.get(widget.id, []),
                                db=db,
                            ).model_dump(),
                            'user': user.model_dump() if user else None,
                        }
                    )
                )
            return widgets

    def get_widgets_by_user_id(
        self, user_id: str, permission: str = 'write', db: Optional[Session] = None
    ) -> list[WidgetUserModel]:
        widgets = self.get_widgets(db=db)
        user_group_ids = {group.id for group in Groups.get_groups_by_member_id(user_id, db=db)}

        return [
            widget
            for widget in widgets
            if widget.user_id == user_id
            or AccessGrants.has_access(
                user_id=user_id,
                resource_type='widget',
                resource_id=widget.id,
                permission=permission,
                user_group_ids=user_group_ids,
                db=db,
            )
        ]

    def search_widgets(
        self,
        user_id: str,
        filter: dict = {},
        skip: int = 0,
        limit: int = 30,
        db: Optional[Session] = None,
    ) -> WidgetListResponse:
        try:
            with get_db_context(db) as db:
                from open_webui.models.users import User, UserModel

                query = db.query(Widget, User).outerjoin(User, User.id == Widget.user_id)

                if filter:
                    query_key = filter.get('query')
                    if query_key:
                        query = query.filter(
                            or_(
                                Widget.name.ilike(f'%{query_key}%'),
                                Widget.description.ilike(f'%{query_key}%'),
                                Widget.id.ilike(f'%{query_key}%'),
                                User.name.ilike(f'%{query_key}%'),
                                User.email.ilike(f'%{query_key}%'),
                            )
                        )

                    view_option = filter.get('view_option')
                    if view_option == 'created':
                        query = query.filter(Widget.user_id == user_id)
                    elif view_option == 'shared':
                        query = query.filter(Widget.user_id != user_id)

                    # Apply access grant filtering
                    query = AccessGrants.has_permission_filter(
                        db=db,
                        query=query,
                        DocumentModel=Widget,
                        filter=filter,
                        resource_type='widget',
                        permission='read',
                    )

                query = query.order_by(Widget.updated_at.desc())

                # Count BEFORE pagination
                total = query.count()

                if skip:
                    query = query.offset(skip)
                if limit:
                    query = query.limit(limit)

                items = query.all()

                widget_ids = [widget.id for widget, _ in items]
                grants_map = AccessGrants.get_grants_by_resources('widget', widget_ids, db=db)

                widgets = []
                for widget, user in items:
                    widgets.append(
                        WidgetUserResponse(
                            **self._to_widget_model(
                                widget,
                                access_grants=grants_map.get(widget.id, []),
                                db=db,
                            ).model_dump(),
                            user=(UserResponse(**UserModel.model_validate(user).model_dump()) if user else None),
                        )
                    )

                return WidgetListResponse(items=widgets, total=total)
        except Exception as e:
            log.exception(f'Error searching widgets: {e}')
            return WidgetListResponse(items=[], total=0)

    def update_widget_by_id(self, id: str, updated: dict, db: Optional[Session] = None) -> Optional[WidgetModel]:
        try:
            with get_db_context(db) as db:
                access_grants = updated.pop('access_grants', None)
                db.query(Widget).filter_by(id=id).update({**updated, 'updated_at': int(time.time())})
                db.commit()
                if access_grants is not None:
                    AccessGrants.set_access_grants('widget', id, access_grants, db=db)

                widget = db.query(Widget).get(id)
                db.refresh(widget)
                return self._to_widget_model(widget, db=db)
        except Exception:
            return None

    def toggle_widget_by_id(self, id: str, db: Optional[Session] = None) -> Optional[WidgetModel]:
        with get_db_context(db) as db:
            try:
                widget = db.query(Widget).filter_by(id=id).first()
                if not widget:
                    return None

                widget.is_active = not widget.is_active
                widget.updated_at = int(time.time())
                db.commit()
                db.refresh(widget)

                return self._to_widget_model(widget, db=db)
            except Exception:
                return None

    def delete_widget_by_id(self, id: str, db: Optional[Session] = None) -> bool:
        try:
            with get_db_context(db) as db:
                AccessGrants.revoke_all_access('widget', id, db=db)
                db.query(Widget).filter_by(id=id).delete()
                db.commit()

                return True
        except Exception:
            return False


Widgets = WidgetsTable()
