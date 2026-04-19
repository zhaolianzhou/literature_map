from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app.db import get_session
from app.db_models import Poet, Poem, PoemLocation, Location, LocationAlias, PoetCreate, PoetRead

router = APIRouter(prefix="/api/poets", tags=["poets"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_location_row(session: Session, loc_name: str) -> Location | None:
    """Look up a location by name or alias."""
    loc = session.exec(select(Location).where(Location.name == loc_name)).first()
    if loc:
        return loc
    alias = session.exec(
        select(LocationAlias).where(LocationAlias.alias == loc_name)
    ).first()
    if alias:
        return session.get(Location, alias.canonical_id)
    return None


def _location_to_dict(loc: Location, display_name: str | None = None) -> dict:
    return {
        "name": display_name or loc.name,
        "ancient_name": loc.ancient or loc.name,
        "modern_name": loc.modern or "",
        "lat": loc.lat,
        "lng": loc.lng,
        "description": loc.description or "",
    }


def _poem_to_dict(poem: Poem, session: Session, include_locations: bool = True) -> dict:
    author_name = poem.author.name if poem.author else ""
    result: dict = {
        "id": poem.id,
        "title": poem.title,
        "author": author_name,
        "dynasty": poem.dynasty,
        "content": poem.content,
        "written_year": poem.written_year,
        "occasion": poem.occasion,
        "locations": [],
        "resolved_locations": [],
    }
    if include_locations:
        links = session.exec(
            select(PoemLocation)
            .where(PoemLocation.poem_id == poem.id)
            .order_by(PoemLocation.mention_order)
        ).all()
        for link in links:
            loc = session.get(Location, link.location_id)
            if loc:
                result["locations"].append(loc.name)
                result["resolved_locations"].append(_location_to_dict(loc))
    return result


def _build_trace(poet_name: str, session: Session) -> list[dict]:
    """
    Build chronological travel trace for a poet from DB.
    Poems sorted by written_year, then id. Locations ordered by mention_order.
    """
    poet = session.exec(select(Poet).where(Poet.name == poet_name)).first()
    if not poet:
        return []

    poems = session.exec(
        select(Poem)
        .where(Poem.author_id == poet.id)
        .order_by(
            func.coalesce(Poem.written_year, 9999),
            Poem.id,
        )
    ).all()

    trace = []
    seq = 0
    seen: set[tuple[int, int]] = set()  # (poem_id, location_id)

    for poem in poems:
        links = session.exec(
            select(PoemLocation)
            .where(PoemLocation.poem_id == poem.id)
            .order_by(PoemLocation.mention_order)
        ).all()

        for link in links:
            key = (poem.id, link.location_id)
            if key in seen:
                continue
            seen.add(key)
            loc = session.get(Location, link.location_id)
            if not loc:
                continue
            trace.append(
                {
                    "sequence": seq,
                    "poem_id": poem.id,
                    "poem_title": poem.title,
                    "year": poem.written_year,
                    "location": _location_to_dict(loc),
                }
            )
            seq += 1

    return trace


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/", response_model=PoetRead, status_code=201)
def create_poet(poet_in: PoetCreate, session: Session = Depends(get_session)):
    """Create a new poet."""
    existing = session.exec(select(Poet).where(Poet.name == poet_in.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Poet '{poet_in.name}' already exists")
    poet = Poet.model_validate(poet_in)
    session.add(poet)
    session.commit()
    session.refresh(poet)
    return poet


@router.get("/")
def list_poets(session: Session = Depends(get_session)):
    """Return all poets with basic info and poem count."""
    poets = session.exec(select(Poet).order_by(func.coalesce(Poet.birth_year, 9999))).all()

    result = []
    for poet in poets:
        poem_count = session.exec(
            select(func.count()).where(Poem.author_id == poet.id)
        ).one()
        result.append(
            {
                "name": poet.name,
                "birth_year": poet.birth_year,
                "death_year": poet.death_year,
                "native_place": poet.native_place,
                "style": poet.style,
                "poem_count": poem_count,
            }
        )

    return {"total": len(result), "poets": result}


@router.get("/{poet_name}")
def get_poet(poet_name: str, session: Session = Depends(get_session)):
    """Return detailed info and all poems for a poet."""
    poet = session.exec(select(Poet).where(Poet.name == poet_name)).first()
    if not poet:
        raise HTTPException(status_code=404, detail=f"Poet '{poet_name}' not found")

    poems = session.exec(
        select(Poem).where(Poem.author_id == poet.id).order_by(
            func.coalesce(Poem.written_year, 9999), Poem.id
        )
    ).all()

    return {
        "name": poet.name,
        "birth_year": poet.birth_year,
        "death_year": poet.death_year,
        "native_place": poet.native_place,
        "biography": poet.biography,
        "style": poet.style,
        "poems": [_poem_to_dict(p, session) for p in poems],
    }


@router.get("/{poet_name}/trace")
def get_poet_trace(poet_name: str, session: Session = Depends(get_session)):
    """Return the chronological travel trace for a poet."""
    poet = session.exec(select(Poet).where(Poet.name == poet_name)).first()
    if not poet:
        raise HTTPException(status_code=404, detail=f"Poet '{poet_name}' not found")

    trace = _build_trace(poet_name, session)

    return {
        "poet": poet.name,
        "birth_year": poet.birth_year,
        "death_year": poet.death_year,
        "native_place": poet.native_place,
        "biography": poet.biography,
        "style": poet.style,
        "trace_count": len(trace),
        "trace": trace,
    }
