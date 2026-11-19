
import os
from dotenv import load_dotenv

load_dotenv()


class CloudflareConfig:

    ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
    ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
    SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
    BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
    ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")

    @classmethod
    def validate(cls):
        required = {
            "R2_ACCOUNT_ID": cls.ACCOUNT_ID,
            "R2_ACCESS_KEY_ID": cls.ACCESS_KEY_ID,
            "R2_SECRET_ACCESS_KEY": cls.SECRET_ACCESS_KEY,
            "R2_BUCKET_NAME": cls.BUCKET_NAME,
            "R2_ENDPOINT_URL": cls.ENDPOINT_URL,
        }

        missing = [
            name for name, value in required.items()
            if not value
        ]

        if missing:
            raise ValueError(
                f"Missing Cloudflare settings: {', '.join(missing)}"
            )


cloudflare_config = CloudflareConfig()
cloudflare_config.validate()
