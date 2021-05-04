from marshmallow import ValidationError, Schema
from aiohttp import web
from typing import Optional, Mapping, NoReturn


class CustomException(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


async def error_handler(
    error: ValidationError,
    req: web.Request,
    schema: Schema,
    error_status_code: Optional[int] = None,
    error_headers: Optional[Mapping[str, str]] = None,
) -> NoReturn:
    raise CustomException(message=error.messages, status=422)


@web.middleware
async def intercept_error(request, handler):
    try:
        return await handler(request)
    except CustomException as e:
        return web.json_response(e.message, status=e.status)
