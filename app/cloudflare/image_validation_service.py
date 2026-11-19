
from io import BytesIO

from PIL import (
    Image,
    UnidentifiedImageError,
    ImageOps
)

from fastapi import HTTPException


class ImageValidationService:

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    MAX_IMAGE_PIXELS = 30_000_000  # 25 megapixels

    ALLOWED_FORMATS = {
        "JPEG",
        "PNG",
        "WEBP"
    }

    def validate_image(self, file_bytes: bytes) -> str:

        # Check empty file
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Image file is empty."
            )

        # Check file size
        if len(file_bytes) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image cannot exceed 10 MB."
            )

        try:
            # Open image
            image = Image.open(BytesIO(file_bytes))

            # Check actual image format
            image_format = image.format

            if image_format not in self.ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail="Only JPEG, PNG and WebP images are allowed."
                )

            # Check image dimensions
            width, height = image.size

            if width * height > self.MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions are too large."
                )

            # Verify image integrity
            image.verify()

            # Reopen and fully decode image
            image = Image.open(BytesIO(file_bytes))
            image.load()

            # Verify orientation handling is possible
            ImageOps.exif_transpose(image)

            return image_format

        except HTTPException:
            raise

        except Image.DecompressionBombWarning:
            raise HTTPException(
                status_code=400,
                detail="Image dimensions are too large."
            )

        except Image.DecompressionBombError:
            raise HTTPException(
                status_code=400,
                detail="Image dimensions are too large."
            )

        except (UnidentifiedImageError, OSError):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid image."
            )

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to validate uploaded image."
            )


image_validation_service = ImageValidationService()
