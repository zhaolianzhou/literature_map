"""
Location resolver: maps place names in poems to lat/lng coordinates.

Primary source:  PostgreSQL locations table (curated Tang Dynasty DB).
Fallback:        OpenStreetMap Nominatim geocoding API.
                 Nominatim results are persisted to the DB so they are
                 only fetched once per unknown place name.

The old in-memory dict approach is preserved as a thin compatibility shim
used during the seed script (before the DB is populated) and in tests.
"""

import httpx
import asyncio
from typing import Optional

from sqlmodel import Session, select

from app.db_models import Location, LocationAlias


# ---------------------------------------------------------------------------
# DB-backed helpers
# ---------------------------------------------------------------------------

def resolve_location_from_db(name: str, session: Session) -> Optional[Location]:
    """Look up a Location row by name or alias."""
    loc = session.exec(select(Location).where(Location.name == name)).first()
    if loc:
        return loc
    alias = session.exec(
        select(LocationAlias).where(LocationAlias.alias == name)
    ).first()
    if alias:
        return session.get(Location, alias.canonical_id)
    return None


# ---------------------------------------------------------------------------
# Nominatim geocoder (with DB persistence)
# ---------------------------------------------------------------------------

async def geocode_nominatim(
    place_name: str,
    session: Optional[Session] = None,
) -> Optional[dict]:
    """
    Geocode via OSM Nominatim. If a Session is provided, the result is
    persisted as a new Location row so subsequent lookups hit the DB.
    Returns a plain dict (compatible with the old API) or None.
    """
    # Check DB first if a session was given
    if session:
        existing = resolve_location_from_db(place_name, session)
        if existing:
            return _loc_row_to_dict(existing)

    query = f"{place_name} China"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "accept-language": "zh-CN",
    }
    headers = {"User-Agent": "AncientChinaLiteratureMap/1.0"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            results = resp.json()
            if results:
                r = results[0]
                entry = {
                    "name": place_name,
                    "lat": float(r["lat"]),
                    "lng": float(r["lon"]),
                    "modern": r.get("display_name", ""),
                    "ancient": place_name,
                    "desc": "Nominatim geocoded",
                }

                # Persist to DB so we never call Nominatim twice for this name
                if session:
                    new_loc = Location(
                        name=place_name,
                        lat=entry["lat"],
                        lng=entry["lng"],
                        modern=entry["modern"],
                        ancient=place_name,
                        description="Nominatim geocoded",
                    )
                    session.add(new_loc)
                    session.commit()
                    session.refresh(new_loc)

                return entry
    except Exception:
        pass

    return None


def _loc_row_to_dict(loc: Location) -> dict:
    return {
        "name": loc.name,
        "lat": loc.lat,
        "lng": loc.lng,
        "modern": loc.modern or "",
        "ancient": loc.ancient or loc.name,
        "desc": loc.description or "",
    }


# ---------------------------------------------------------------------------
# Backward-compatible helpers (used by seed.py and any legacy callers)
# These fall back to the static Python dict when no DB session is available.
# ---------------------------------------------------------------------------

def resolve_poem_locations(location_names: list[str]) -> list[dict]:
    """
    Resolve location names using the curated static dict (no DB session).
    Used by the seed script before the DB is populated.
    """
    from app.data.locations_db import get_location

    resolved = []
    seen: set[str] = set()
    for name in location_names:
        if name in seen:
            continue
        seen.add(name)
        loc = get_location(name)
        if loc:
            resolved.append(loc)
    return resolved


def extract_locations_from_text(text: str) -> list[str]:
    """Keyword scan of poem content for known place names (static dict)."""
    from app.data.locations_db import TANG_LOCATIONS, LOCATION_ALIASES

    found: list[str] = []
    all_names = set(TANG_LOCATIONS.keys()) | set(LOCATION_ALIASES.keys())
    for name in all_names:
        if name in text:
            canonical = LOCATION_ALIASES.get(name, name)
            if canonical not in found:
                found.append(canonical)
    return found
