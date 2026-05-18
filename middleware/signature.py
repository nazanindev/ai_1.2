import hashlib
import hmac

from fastapi import HTTPException, Request


async def verify_github_signature(request: Request, secret: str) -> bytes:
    """Read body, verify X-Hub-Signature-256 header, return raw body."""
    body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")

    if not secret:
        return body

    if not sig_header.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Missing or malformed signature")

    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(status_code=403, detail="Invalid signature")

    return body
