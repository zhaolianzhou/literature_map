"""
Seed script — migrates static Python data into the PostgreSQL database.

Run once after the database is up:
    poetry run python seed.py

Or inside Docker after the stack is running:
    docker compose exec backend python seed.py

The script is idempotent: running it a second time will skip rows that
already exist (matched by unique name / title+author_id).
"""

import os
import sys
from sqlmodel import Session, select

# Ensure the app package is on the path when run from the backend/ directory.
sys.path.insert(0, os.path.dirname(__file__))

from app.db import engine, create_db_and_tables
from app.db_models import (
    Location,
    LocationAlias,
    Poet,
    Poem,
    PoemLocation,
)
from app.data.poems_data import POEMS, POETS
from app.data.locations_db import TANG_LOCATIONS, LOCATION_ALIASES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upsert_poet(session: Session, name: str, info: dict) -> Poet:
    existing = session.exec(select(Poet).where(Poet.name == name)).first()
    if existing:
        return existing
    poet = Poet(
        name=name,
        birth_year=info.get("birth_year"),
        death_year=info.get("death_year"),
        native_place=info.get("native_place"),
        biography=info.get("biography"),
        style=info.get("style"),
    )
    session.add(poet)
    session.flush()  # assigns poet.id without committing
    return poet


def _upsert_location(session: Session, name: str, info: dict) -> Location:
    existing = session.exec(select(Location).where(Location.name == name)).first()
    if existing:
        return existing
    loc = Location(
        name=name,
        lat=info["lat"],
        lng=info["lng"],
        modern=info.get("modern"),
        ancient=info.get("ancient"),
        description=info.get("desc"),
    )
    session.add(loc)
    session.flush()
    return loc


def _upsert_alias(session: Session, alias: str, canonical: Location) -> None:
    existing = session.exec(
        select(LocationAlias).where(LocationAlias.alias == alias)
    ).first()
    if existing:
        return
    session.add(LocationAlias(alias=alias, canonical_id=canonical.id))


def _upsert_poem(session: Session, data: dict, author: Poet) -> Poem:
    existing = session.exec(
        select(Poem).where(Poem.title == data["title"], Poem.author_id == author.id)
    ).first()
    if existing:
        return existing
    poem = Poem(
        title=data["title"],
        author_id=author.id,
        dynasty=data.get("dynasty", "唐"),
        content=data["content"],
        written_year=data.get("written_year"),
        occasion=data.get("occasion"),
    )
    session.add(poem)
    session.flush()
    return poem


def _upsert_poem_location(
    session: Session, poem: Poem, location: Location, order: int
) -> None:
    existing = session.exec(
        select(PoemLocation).where(
            PoemLocation.poem_id == poem.id,
            PoemLocation.location_id == location.id,
        )
    ).first()
    if existing:
        return
    session.add(
        PoemLocation(poem_id=poem.id, location_id=location.id, mention_order=order)
    )


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_locations(session: Session) -> dict[str, Location]:
    """Insert all curated locations. Returns name→Location map."""
    print("Seeding locations...")
    loc_map: dict[str, Location] = {}
    for name, info in TANG_LOCATIONS.items():
        loc = _upsert_location(session, name, info)
        loc_map[name] = loc
    print(f"  {len(loc_map)} locations ready.")
    return loc_map


def seed_aliases(session: Session, loc_map: dict[str, Location]) -> None:
    """Insert location aliases, skipping aliases whose canonical is missing."""
    print("Seeding location aliases...")
    count = 0
    for alias, canonical_name in LOCATION_ALIASES.items():
        canonical = loc_map.get(canonical_name)
        if canonical is None:
            print(f"  Warning: alias '{alias}' → '{canonical_name}' not found, skipping.")
            continue
        _upsert_alias(session, alias, canonical)
        count += 1
    print(f"  {count} aliases ready.")


def seed_poets(session: Session) -> dict[str, Poet]:
    """Insert all poets. Returns name→Poet map."""
    print("Seeding poets...")
    poet_map: dict[str, Poet] = {}
    for name, info in POETS.items():
        poet = _upsert_poet(session, name, info)
        poet_map[name] = poet
    print(f"  {len(poet_map)} poets ready.")
    return poet_map


def seed_poems(
    session: Session,
    poet_map: dict[str, Poet],
    loc_map: dict[str, Location],
) -> None:
    """Insert poems and their location associations."""
    print("Seeding poems and poem_locations...")
    poem_count = 0
    link_count = 0
    skipped_locs: list[str] = []

    for data in POEMS:
        author_name = data["author"]
        author = poet_map.get(author_name)
        if author is None:
            print(f"  Warning: poet '{author_name}' not in POETS dict, skipping poem '{data['title']}'.")
            continue

        poem = _upsert_poem(session, data, author)
        poem_count += 1

        for order, loc_name in enumerate(data.get("locations", [])):
            # Resolve alias → canonical
            canonical_name = LOCATION_ALIASES.get(loc_name, loc_name)
            location = loc_map.get(canonical_name)
            if location is None:
                # Try without alias resolution
                location = loc_map.get(loc_name)
            if location is None:
                skipped_locs.append(f"poem '{data['title']}' → '{loc_name}'")
                continue
            _upsert_poem_location(session, poem, location, order)
            link_count += 1

    print(f"  {poem_count} poems ready, {link_count} location links created.")
    if skipped_locs:
        print(f"  Unresolved locations ({len(skipped_locs)}):")
        for s in skipped_locs:
            print(f"    - {s}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Creating tables (if not exist)...")
    create_db_and_tables()

    with Session(engine) as session:
        loc_map = seed_locations(session)
        seed_aliases(session, loc_map)
        poet_map = seed_poets(session)
        seed_poems(session, poet_map, loc_map)
        session.commit()

    print("\nSeed complete.")


if __name__ == "__main__":
    main()
