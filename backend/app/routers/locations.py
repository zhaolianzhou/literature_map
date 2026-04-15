from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.db import get_session
from app.db_models import Location, LocationAlias, Poem, PoemLocation, Poet
from app.location_resolver import geocode_nominatim

router = APIRouter(prefix="/api/locations", tags=["locations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _location_to_dict(loc: Location, poem_count: int = 0) -> dict:
    return {
        "name": loc.name,
        "ancient_name": loc.ancient or loc.name,
        "modern_name": loc.modern or "",
        "lat": loc.lat,
        "lng": loc.lng,
        "description": loc.description or "",
        "poem_count": poem_count,
    }


def _resolve_location(session: Session, name: str) -> Location | None:
    """Look up a Location by name, then by alias."""
    loc = session.exec(select(Location).where(Location.name == name)).first()
    if loc:
        return loc
    alias = session.exec(
        select(LocationAlias).where(LocationAlias.alias == name)
    ).first()
    if alias:
        return session.get(Location, alias.canonical_id)
    return None


def _poem_count_for(session: Session, location_id: int) -> int:
    return session.exec(
        select(func.count()).where(PoemLocation.location_id == location_id)
    ).one()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/")
def list_locations(session: Session = Depends(get_session)):
    """Return all curated Tang Dynasty locations with poem counts."""
    locations = session.exec(select(Location)).all()
    result = []
    for loc in locations:
        count = _poem_count_for(session, loc.id)
        result.append(_location_to_dict(loc, count))
    result.sort(key=lambda x: -x["poem_count"])
    return {"total": len(result), "locations": result}


@router.get("/geocode")
async def geocode(
    place: str = Query(..., description="Place name to geocode"),
    session: Session = Depends(get_session),
):
    """
    Geocode a place name: check DB first (name + aliases), then Nominatim fallback.
    Nominatim results are persisted to the DB as new locations.
    """
    loc = _resolve_location(session, place)
    if loc:
        return {"source": "curated", "location": _location_to_dict(loc)}

    result = await geocode_nominatim(place, session)
    if result:
        # Return the freshly-persisted location
        new_loc = _resolve_location(session, place)
        if new_loc:
            return {"source": "nominatim", "location": _location_to_dict(new_loc)}
        return {"source": "nominatim", "location": result}

    raise HTTPException(status_code=404, detail=f"Could not geocode '{place}'")


@router.get("/heatmap")
def location_heatmap(session: Session = Depends(get_session)):
    """
    Return all locations that appear in at least one poem, with poem count as weight.
    """
    rows = session.exec(
        select(PoemLocation.location_id, func.count().label("cnt"))
        .group_by(PoemLocation.location_id)
        .order_by(func.count().desc())
    ).all()

    heatmap = []
    for location_id, count in rows:
        loc = session.get(Location, location_id)
        if loc:
            heatmap.append(
                {
                    "name": loc.name,
                    "lat": loc.lat,
                    "lng": loc.lng,
                    "weight": count,
                    "modern": loc.modern or "",
                }
            )

    return {"total": len(heatmap), "heatmap": heatmap}


@router.get("/{location_name}/poems")
def poems_at_location(
    location_name: str,
    session: Session = Depends(get_session),
):
    """Return all poems associated with a specific location."""
    loc = _resolve_location(session, location_name)
    if not loc:
        raise HTTPException(
            status_code=404, detail=f"Location '{location_name}' not found"
        )

    poem_ids = session.exec(
        select(PoemLocation.poem_id).where(PoemLocation.location_id == loc.id)
    ).all()

    poems = []
    for pid in poem_ids:
        poem = session.get(Poem, pid)
        if poem:
            author_name = poem.author.name if poem.author else ""
            poems.append(
                {
                    "id": poem.id,
                    "title": poem.title,
                    "author": author_name,
                    "dynasty": poem.dynasty,
                    "content": poem.content,
                    "written_year": poem.written_year,
                    "occasion": poem.occasion,
                }
            )

    return {
        "location": _location_to_dict(loc, len(poems)),
        "poem_count": len(poems),
        "poems": poems,
    }
