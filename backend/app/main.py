import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import poems, poets, locations

app = FastAPI(
    title="Ancient China Literature Map API",
    description="Travel traces of Tang Dynasty poets from 唐诗三百首",
    version="1.0.0",
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
def stats():
    """High-level statistics about the dataset."""
    from app.data.poems_data import POEMS, POETS
    from app.data.locations_db import TANG_LOCATIONS

    location_set = set()
    for poem in POEMS:
        for loc in poem.get("locations", []):
            location_set.add(loc)

    return {
        "total_poems": len(POEMS),
        "total_poets": len(POETS),
        "total_locations_db": len(TANG_LOCATIONS),
        "total_unique_locations_in_poems": len(location_set),
        "dynasties": ["唐"],
        "time_span": "618–907 AD",
    }
