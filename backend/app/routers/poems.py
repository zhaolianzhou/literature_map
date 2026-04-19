from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, or_
from typing import Optional
from pydantic import BaseModel

from app.db import get_session
from app.db_models import Poet, Poem, PoemLocation, Location, LocationAlias, PoemRead

router = APIRouter(prefix="/api/poems", tags=["poems"])


class PoemCreateInput(BaseModel):
    """User-facing poem creation payload (uses author name instead of author_id)."""
    title: str
    author_name: str
    dynasty: str = "唐"
    content: str
    written_year: Optional[int] = None
    occasion: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _location_to_dict(loc: Location) -> dict:
    return {
        "name": loc.name,
        "ancient_name": loc.ancient or loc.name,
        "modern_name": loc.modern or "",
        "lat": loc.lat,
        "lng": loc.lng,
        "description": loc.description or "",
    }


def _poem_to_dict(poem: Poem, session: Session) -> dict:
    links = session.exec(
        select(PoemLocation)
        .where(PoemLocation.poem_id == poem.id)
        .order_by(PoemLocation.mention_order)
    ).all()
    location_names: list[str] = []
    resolved_locations: list[dict] = []
    for link in links:
        loc = session.get(Location, link.location_id)
        if loc:
            location_names.append(loc.name)
            resolved_locations.append(_location_to_dict(loc))

    author_name = poem.author.name if poem.author else ""
    return {
        "id": poem.id,
        "title": poem.title,
        "author": author_name,
        "dynasty": poem.dynasty,
        "content": poem.content,
        "written_year": poem.written_year,
        "occasion": poem.occasion,
        "locations": location_names,
        "resolved_locations": resolved_locations,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/", response_model=PoemRead, status_code=201)
def create_poem(poem_in: PoemCreateInput, session: Session = Depends(get_session)):
    """Create a new poem. Author is looked up by name."""
    poet = session.exec(select(Poet).where(Poet.name == poem_in.author_name)).first()
    if not poet:
        raise HTTPException(status_code=404, detail=f"Poet '{poem_in.author_name}' not found")
    poem = Poem(
        title=poem_in.title,
        author_id=poet.id,
        dynasty=poem_in.dynasty,
        content=poem_in.content,
        written_year=poem_in.written_year,
        occasion=poem_in.occasion,
    )
    session.add(poem)
    session.commit()
    session.refresh(poem)
    return poem


@router.get("/search/locations")
def poems_by_location(
    place: str = Query(..., description="Place name to search"),
    session: Session = Depends(get_session),
):
    """Find all poems that mention a given location (by name or alias)."""
    # Resolve alias → canonical location
    loc = session.exec(select(Location).where(Location.name == place)).first()
    if not loc:
        alias = session.exec(
            select(LocationAlias).where(LocationAlias.alias == place)
        ).first()
        if alias:
            loc = session.get(Location, alias.canonical_id)

    if not loc:
        return {"place": place, "count": 0, "poems": []}

    poem_ids = session.exec(
        select(PoemLocation.poem_id).where(PoemLocation.location_id == loc.id)
    ).all()

    poems = []
    for pid in poem_ids:
        poem = session.get(Poem, pid)
        if poem:
            poems.append(_poem_to_dict(poem, session))

    return {"place": place, "count": len(poems), "poems": poems}


@router.get("/")
def list_poems(
    author: str | None = Query(None, description="Filter by poet name"),
    location: str | None = Query(None, description="Filter by location name"),
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """Return all poems, optionally filtered by author or location."""
    stmt = select(Poem).order_by(func.coalesce(Poem.written_year, 9999), Poem.id)

    if author:
        poet = session.exec(select(Poet).where(Poet.name.contains(author))).first()
        if poet:
            stmt = stmt.where(Poem.author_id == poet.id)
        else:
            return {"total": 0, "poems": []}

    if location:
        # Find matching location (name or alias)
        loc = session.exec(
            select(Location).where(Location.name.contains(location))
        ).first()
        if loc:
            poem_ids = session.exec(
                select(PoemLocation.poem_id).where(PoemLocation.location_id == loc.id)
            ).all()
            stmt = stmt.where(Poem.id.in_(poem_ids))
        else:
            return {"total": 0, "poems": []}

    all_poems = session.exec(stmt).all()
    total = len(all_poems)
    page = all_poems[skip: skip + limit]

    return {"total": total, "poems": [_poem_to_dict(p, session) for p in page]}


@router.get("/{poem_id}")
def get_poem(poem_id: int, session: Session = Depends(get_session)):
    """Return a single poem by ID."""
    poem = session.get(Poem, poem_id)
    if not poem:
        raise HTTPException(status_code=404, detail=f"Poem {poem_id} not found")
    return _poem_to_dict(poem, session)
