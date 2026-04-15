import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func

from app.routers import poems, poets, locations
from app.db import create_db_and_tables, get_session
from app.db_models import Poem, Poet, Location, PoemLocation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (idempotent — safe to run repeatedly).
    In production, prefer Alembic migrations over this auto-create approach."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Ancient China Literature Map API",
    description="Travel traces of Tang Dynasty poets from 唐诗三百首",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(poems.router)
app.include_router(poets.router)
app.include_router(locations.router)


@app.get("/")
def root():
    return {
        "app": "Ancient China Literature Map",
        "description": "唐诗三百首 — Poet travel traces on the map",
        "docs": "/docs",
        "endpoints": {
            "poets": "/api/poets",
            "poems": "/api/poems",
            "locations": "/api/locations",
        },
    }


@app.get("/api/stats")
def stats(session: Session = Depends(get_session)):
    """High-level statistics about the dataset, sourced from the database."""
    total_poems = session.exec(select(func.count()).select_from(Poem)).one()
    total_poets = session.exec(select(func.count()).select_from(Poet)).one()
    total_locations_db = session.exec(select(func.count()).select_from(Location)).one()
    total_unique_locations_in_poems = session.exec(
        select(func.count(func.distinct(PoemLocation.location_id)))
    ).one()

    return {
        "total_poems": total_poems,
        "total_poets": total_poets,
        "total_locations_db": total_locations_db,
        "total_unique_locations_in_poems": total_unique_locations_in_poems,
        "dynasties": ["唐"],
        "time_span": "618–907 AD",
    }
