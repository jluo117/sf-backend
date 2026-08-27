from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.schemas import ProfilePictureUpload

router = APIRouter(prefix="/api/v1/media", tags=["media"])
settings = get_settings()

PROFILE_PICTURE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.post(
    "/profile-picture",
    response_model=ProfilePictureUpload,
    operation_id="uploadProfilePicture",
    summary="Upload a profile picture",
    response_description="The public URL of the uploaded picture.",
)
async def upload_profile_picture(
    picture: UploadFile = File(description="JPEG, PNG, WebP, or GIF image, up to 5 MB."),
) -> ProfilePictureUpload:
    """Store an image and return its public URL for a JSON contact request."""
    extension = PROFILE_PICTURE_TYPES.get(picture.content_type or "")
    if extension is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Profile picture must be a JPEG, PNG, WebP, or GIF",
        )

    contents = await picture.read(settings.max_profile_picture_bytes + 1)
    if len(contents) > settings.max_profile_picture_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "Profile picture must be 5 MB or smaller",
        )

    filename = f"{uuid4().hex}{extension}"
    destination = Path(settings.media_dir) / "profile-pictures" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_bytes(contents)
    except Exception:
        try:
            destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return ProfilePictureUpload(profile_picture=f"/media/profile-pictures/{filename}")