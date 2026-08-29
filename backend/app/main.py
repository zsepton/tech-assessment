import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data_access.customers import load_customers
from app.logging_config import configure_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.routes.customers import router as customers_router
from app.routes.model_info import router as model_info_router

configure_logging()

ALLOWED_ORIGINS = ["http://localhost:5173"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.customers = await asyncio.to_thread(load_customers)
    yield


app = FastAPI(title="Churn Risk & Retention Console API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(customers_router)
app.include_router(model_info_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
