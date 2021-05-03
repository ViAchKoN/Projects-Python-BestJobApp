from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)

from settings import CONFIG
from routes import setup_routes
from db import init_pg

app = web.Application()
setup_routes(app)

app['config'] = CONFIG
app.on_startup.append(init_pg)

setup_aiohttp_apispec(app, swagger_path="/docs")
app.middlewares.append(validation_middleware)

web.run_app(app)
