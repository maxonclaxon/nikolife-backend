"""
In this module FastAPI application is initializing.
"""

import sentry_sdk
import fastapi


from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.admin import create_admin
from app.api.routes.root import router
from app.config import Settings
from app.utils.utility import create_superuser

sentry_settings = Settings().sentry
if sentry_settings:
    sentry_sdk.init(
        dsn=sentry_settings.dsn,
        environment=Settings().environment,
        integrations=[SqlalchemyIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,
    )

app = fastapi.FastAPI()
app.include_router(router)
create_admin(app)


@app.on_event("startup")
async def startup():
    """startup methods for FastAPI application"""
    Instrumentator().instrument(app).expose(app)
    if Settings().environment == "development":
        await create_superuser()
