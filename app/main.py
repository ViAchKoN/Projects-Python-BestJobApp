from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)

from settings import CONFIG
from routes import setup_routes
from db import init_pg
from utils import error_handler, intercept_error

app = web.Application()
setup_routes(app)

app['config'] = CONFIG
app.on_startup.append(init_pg)

setup_aiohttp_apispec(app, error_callback=error_handler, swagger_path="/docs")
app.middlewares.extend([intercept_error, validation_middleware])

web.run_app(app)
