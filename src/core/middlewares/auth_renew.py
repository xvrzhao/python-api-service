from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthRenewMiddleware(BaseHTTPMiddleware):
    """
    After the request handler runs, check if the auth dependency generated
    a new access token (stored in request.state.new_access_token).

    If so, expose it to the frontend via the X-New-Access-Token response header.
    The frontend's authFetch wrapper reads this header and updates localStorage
    transparently — the user never knows a renewal happened.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        new_token = getattr(request.state, "new_access_token", None)
        if new_token:
            response.headers["X-New-Access-Token"] = new_token
        return response
