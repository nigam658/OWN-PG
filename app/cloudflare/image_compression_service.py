
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException


class ImageCompressionService:

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

    IMAGE_SETTINGS = {
        "profile": {
            "max_dimension": 800,
            "target_size": 200 * 1024,  # 200 KB
        },
        "document": {
            "max_dimension": 1600,
            "target_size": 500 * 1024,  # 500 KB
        },
    }

    # Compress profile photos and document images
    def compress_image(
        self,
        file_bytes: bytes,
        image_type: str = "profile"
    ) -> bytes:

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Image file is empty."
            )

        if len(file_bytes) > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image must not exceed 10 MB."
            )

        if image_type not in self.IMAGE_SETTINGS:
            raise HTTPException(
                status_code=400,
                detail="Unsupported image type."
            )

        try:
            # Open image and check its actual format
            image = Image.open(BytesIO(file_bytes))

            if image.format not in self.ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail="Only JPEG, PNG and WebP images are allowed."
                )

            # Reject decompression bomb warnings/errors
            image.verify()

            # Reopen image after verification
            image = Image.open(BytesIO(file_bytes))

            # Apply correct image orientation
            image = ImageOps.exif_transpose(image)

            # Get settings for the requested image type
            settings = self.IMAGE_SETTINGS[image_type]

            max_dimension = settings["max_dimension"]
            target_size = settings["target_size"]

            # Resize while preserving aspect ratio
            image.thumbnail(
                (max_dimension, max_dimension),
                Image.Resampling.LANCZOS
            )

            # Convert transparent images to white background
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGBA")

                background = Image.new(
                    "RGB",
                    image.size,
                    (255, 255, 255)
                )

                background.paste(
                    image,
                    mask=image.getchannel("A")
                )

                image = background

            else:
                image = image.convert("RGB")

            compressed = b""

            # Reduce JPEG quality until target size is reached
            for quality in range(90, 29, -5):

                output = BytesIO()

                image.save(
                    output,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )

                compressed = output.getvalue()

                if len(compressed) <= target_size:
                    break

            return compressed

        except HTTPException:
            raise

        except (UnidentifiedImageError, OSError):
            raise HTTPException(
                status_code=400,
                detail="Invalid or unsupported image."
            )

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to process image."
            )


image_compression_service = ImageCompressionService()
