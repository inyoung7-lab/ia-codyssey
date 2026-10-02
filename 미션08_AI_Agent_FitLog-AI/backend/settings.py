"""Public deployment settings; never echo invalid environment values."""
import os
from urllib.parse import urlsplit


def allowed_origins():
    origins = ["http://127.0.0.1:5500", "http://localhost:5500"]
    for item in os.getenv("ALLOWED_ORIGINS", "").split(","):
        origin = item.strip().rstrip("/")
        if not origin:
            continue
        try:
            url = urlsplit(origin)
            valid = (url.scheme in {"http", "https"} and url.hostname
                     and not url.username and not url.password and not url.path
                     and not url.query and not url.fragment and "*" not in origin
                     and not any(c.isspace() for c in origin))
            _ = url.port
            if not valid:
                raise ValueError()
        except ValueError:
            raise RuntimeError("ALLOWED_ORIGINS must contain comma-separated HTTP(S) origins.") from None
        if origin not in origins:
            origins.append(origin)
    return origins
