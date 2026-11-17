from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.api.v1.access import get_attachment_for_user, get_task_for_user
from app.api.v1.attachments.schemas import AttachmentRead
from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.models.attachment import Attachment
from app.services.file_storage import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    delete_file,
    get_file_path,
    save_upload,
)

router = APIRouter(tags=["attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_attachment(task_id: int, file: UploadFile, db: DbSession, current_user: CurrentUser) -> Attachment:
    task = get_task_for_user(db, task_id, current_user)
    try:
        stored_name, size = save_upload(file)
    except UnsupportedFileTypeError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipo de archivo no permitido",
        )
    except FileTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo supera los {settings.max_upload_size_mb} MB",
        )

    attachment = Attachment(
        task_id=task.id,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        size=size,
        uploaded_by_id=current_user.id,
    )
    db.add(attachment)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_file(stored_name)
        raise
    db.refresh(attachment)
    return attachment


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(task_id: int, db: DbSession, current_user: CurrentUser) -> list[Attachment]:
    task = get_task_for_user(db, task_id, current_user)
    return task.attachments


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, db: DbSession, current_user: CurrentUser) -> FileResponse:
    attachment = get_attachment_for_user(db, attachment_id, current_user)
    path = get_file_path(attachment.stored_name)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El archivo ya no está disponible")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_name)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(attachment_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    attachment = get_attachment_for_user(db, attachment_id, current_user)
    if attachment.uploaded_by_id != current_user.id and not attachment.task.project.is_owner(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien subió el archivo o el dueño del proyecto pueden eliminarlo",
        )
    stored_name = attachment.stored_name
    db.delete(attachment)
    db.commit()
    delete_file(stored_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
