import logging
from typing import Optional

from open_webui.models.groups import Groups
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from open_webui.internal.db import get_session
from open_webui.models.widgets import (
    WidgetForm,
    WidgetModel,
    WidgetResponse,
    WidgetUserResponse,
    WidgetAccessResponse,
    WidgetAccessListResponse,
    Widgets,
)
from open_webui.models.access_grants import AccessGrants
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_permission, filter_allowed_access_grants

from open_webui.config import BYPASS_ADMIN_ACCESS_CONTROL
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)

PAGE_ITEM_COUNT = 30

router = APIRouter()


############################
# GetWidgets
############################


@router.get('/', response_model=list[WidgetUserResponse])
async def get_widgets(
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL:
        widgets = Widgets.get_widgets(db=db)
    else:
        user_group_ids = {group.id for group in Groups.get_groups_by_member_id(user.id, db=db)}
        all_widgets = Widgets.get_widgets(db=db)
        widgets = [
            widget
            for widget in all_widgets
            if widget.user_id == user.id
            or AccessGrants.has_access(
                user_id=user.id,
                resource_type='widget',
                resource_id=widget.id,
                permission='read',
                user_group_ids=user_group_ids,
                db=db,
            )
        ]

    return widgets


############################
# GetWidgetList
############################


@router.get('/list', response_model=WidgetAccessListResponse)
async def get_widget_list(
    query: Optional[str] = None,
    view_option: Optional[str] = None,
    page: Optional[int] = 1,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    limit = PAGE_ITEM_COUNT

    page = max(1, page)
    skip = (page - 1) * limit

    filter = {}
    if query:
        filter['query'] = query
    if view_option:
        filter['view_option'] = view_option

    if not (user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL):
        groups = Groups.get_groups_by_member_id(user.id, db=db)
        if groups:
            filter['group_ids'] = [group.id for group in groups]

        filter['user_id'] = user.id

    result = Widgets.search_widgets(user.id, filter=filter, skip=skip, limit=limit, db=db)

    return WidgetAccessListResponse(
        items=[
            WidgetAccessResponse(
                **widget.model_dump(),
                write_access=(
                    (user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL)
                    or user.id == widget.user_id
                    or AccessGrants.has_access(
                        user_id=user.id,
                        resource_type='widget',
                        resource_id=widget.id,
                        permission='write',
                        db=db,
                    )
                ),
            )
            for widget in result.items
        ],
        total=result.total,
    )


############################
# ExportWidgets
############################


@router.get('/export', response_model=list[WidgetModel])
async def export_widgets(
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if user.role != 'admin' and not has_permission(
        user.id,
        'workspace.widgets',
        request.app.state.config.USER_PERMISSIONS,
        db=db,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    if user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL:
        return Widgets.get_widgets(db=db)
    else:
        return Widgets.get_widgets_by_user_id(user.id, 'read', db=db)


############################
# CreateNewWidget
############################


@router.post('/create', response_model=Optional[WidgetResponse])
async def create_new_widget(
    request: Request,
    form_data: WidgetForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if user.role != 'admin' and not has_permission(
        user.id, 'workspace.widgets', request.app.state.config.USER_PERMISSIONS, db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    form_data.id = form_data.id.lower().replace(' ', '-')

    existing = Widgets.get_widget_by_id(form_data.id, db=db)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.ID_TAKEN,
        )

    try:
        widget = Widgets.insert_new_widget(user.id, form_data, db=db)
        if widget:
            return widget
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT('Error creating widget'),
            )
    except Exception as e:
        log.exception(f'Failed to create widget: {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(str(e)),
        )


############################
# GetWidgetById
############################


@router.get('/id/{id}', response_model=Optional[WidgetAccessResponse])
async def get_widget_by_id(id: str, user=Depends(get_verified_user), db: Session = Depends(get_session)):
    widget = Widgets.get_widget_by_id(id, db=db)

    if widget:
        if (
            user.role == 'admin'
            or widget.user_id == user.id
            or AccessGrants.has_access(
                user_id=user.id,
                resource_type='widget',
                resource_id=widget.id,
                permission='read',
                db=db,
            )
        ):
            return WidgetAccessResponse(
                **widget.model_dump(),
                write_access=(
                    (user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL)
                    or user.id == widget.user_id
                    or AccessGrants.has_access(
                        user_id=user.id,
                        resource_type='widget',
                        resource_id=widget.id,
                        permission='write',
                        db=db,
                    )
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateWidgetById
############################


@router.post('/id/{id}/update', response_model=Optional[WidgetModel])
async def update_widget_by_id(
    request: Request,
    id: str,
    form_data: WidgetForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    widget = Widgets.get_widget_by_id(id, db=db)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        widget.user_id != user.id
        and not AccessGrants.has_access(
            user_id=user.id,
            resource_type='widget',
            resource_id=widget.id,
            permission='write',
            db=db,
        )
        and user.role != 'admin'
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    try:
        updated = {
            **form_data.model_dump(exclude={'id'}),
        }

        widget = Widgets.update_widget_by_id(id, updated, db=db)

        if widget:
            return widget
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT('Error updating widget'),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(str(e)),
        )


############################
# UpdateWidgetAccessById
############################


class WidgetAccessGrantsForm(BaseModel):
    access_grants: list[dict]


@router.post('/id/{id}/access/update', response_model=Optional[WidgetModel])
async def update_widget_access_by_id(
    request: Request,
    id: str,
    form_data: WidgetAccessGrantsForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    widget = Widgets.get_widget_by_id(id, db=db)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        widget.user_id != user.id
        and not AccessGrants.has_access(
            user_id=user.id,
            resource_type='widget',
            resource_id=widget.id,
            permission='write',
            db=db,
        )
        and user.role != 'admin'
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    form_data.access_grants = filter_allowed_access_grants(
        request.app.state.config.USER_PERMISSIONS,
        user.id,
        user.role,
        form_data.access_grants,
        'sharing.public_widgets',
    )

    AccessGrants.set_access_grants('widget', id, form_data.access_grants, db=db)

    return Widgets.get_widget_by_id(id, db=db)


############################
# ToggleWidgetById
############################


@router.post('/id/{id}/toggle', response_model=Optional[WidgetModel])
async def toggle_widget_by_id(id: str, user=Depends(get_verified_user), db: Session = Depends(get_session)):
    widget = Widgets.get_widget_by_id(id, db=db)
    if widget:
        if (
            user.role == 'admin'
            or widget.user_id == user.id
            or AccessGrants.has_access(
                user_id=user.id,
                resource_type='widget',
                resource_id=widget.id,
                permission='write',
                db=db,
            )
        ):
            widget = Widgets.toggle_widget_by_id(id, db=db)

            if widget:
                return widget
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT('Error toggling widget'),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# DeleteWidgetById
############################


@router.delete('/id/{id}/delete', response_model=bool)
async def delete_widget_by_id(
    request: Request,
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    widget = Widgets.get_widget_by_id(id, db=db)
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        widget.user_id != user.id
        and not AccessGrants.has_access(
            user_id=user.id,
            resource_type='widget',
            resource_id=widget.id,
            permission='write',
            db=db,
        )
        and user.role != 'admin'
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = Widgets.delete_widget_by_id(id, db=db)
    return result
