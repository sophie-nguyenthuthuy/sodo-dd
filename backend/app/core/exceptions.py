from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error with a stable error code."""

    code: str = "internal_error"
    default_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        super().__init__(
            status_code=self.default_status,
            detail={"code": code or self.code, "message": message or self.code},
        )


class NotFound(AppError):
    code = "not_found"
    default_status = status.HTTP_404_NOT_FOUND


class Forbidden(AppError):
    code = "forbidden"
    default_status = status.HTTP_403_FORBIDDEN


class Unauthorized(AppError):
    code = "unauthorized"
    default_status = status.HTTP_401_UNAUTHORIZED


class Conflict(AppError):
    code = "conflict"
    default_status = status.HTTP_409_CONFLICT


class BadRequest(AppError):
    code = "bad_request"
    default_status = status.HTTP_400_BAD_REQUEST


class RateLimited(AppError):
    code = "rate_limited"
    default_status = status.HTTP_429_TOO_MANY_REQUESTS


class UpstreamUnavailable(AppError):
    code = "upstream_unavailable"
    default_status = status.HTTP_502_BAD_GATEWAY
