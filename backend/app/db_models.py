"""
SQLModel ORM models — one class serves as both the SQLAlchemy table definition
and the Pydantic schema for serialization.

Table relationships:
  Poet      1──* Poem          (author_id FK)
  Location  1──* LocationAlias (canonical_id FK)
  Poem      *──* Location      via PoemLocation join table
"""

from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


# ---------------------------------------------------------------------------
# Poet
# ---------------------------------------------------------------------------

class PoetBase(SQLModel):
    name: str = Field(index=True, unique=True, max_length=20)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    native_place: Optional[str] = Field(default=None, max_length=100)
    biography: Optional[str] = None
    style: Optional[str] = Field(default=None, max_length=50)


class Poet(PoetBase, table=True):
    __tablename__ = "poets"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    poems: list["Poem"] = Relationship(back_populates="author")


class PoetRead(PoetBase):
    id: int


class PoetCreate(PoetBase):
    pass


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

class LocationBase(SQLModel):
    name: str = Field(index=True, unique=True, max_length=50)
    lat: float
    lng: float
    modern: Optional[str] = Field(default=None, max_length=100)
    ancient: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class Location(LocationBase, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    aliases: list["LocationAlias"] = Relationship(back_populates="canonical")
    poem_links: list["PoemLocation"] = Relationship(back_populates="location")


class LocationRead(LocationBase):
    id: int


class LocationCreate(LocationBase):
    pass


# ---------------------------------------------------------------------------
# LocationAlias
# ---------------------------------------------------------------------------

class LocationAliasBase(SQLModel):
    alias: str = Field(index=True, unique=True, max_length=50)
    canonical_id: int = Field(foreign_key="locations.id")


class LocationAlias(LocationAliasBase, table=True):
    __tablename__ = "location_aliases"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    canonical: Optional[Location] = Relationship(back_populates="aliases")


class LocationAliasRead(LocationAliasBase):
    id: int


class LocationAliasCreate(LocationAliasBase):
    pass


# ---------------------------------------------------------------------------
# PoemLocation  (join table — Poem ↔ Location)
# ---------------------------------------------------------------------------

class PoemLocation(SQLModel, table=True):
    __tablename__ = "poem_locations"

    poem_id: int = Field(foreign_key="poems.id", primary_key=True)
    location_id: int = Field(foreign_key="locations.id", primary_key=True)
    # Preserves the original order of locations listed in the poem,
    # which is used to reconstruct the poet's travel trace.
    mention_order: int = Field(default=0)

    # Relationships
    poem: Optional["Poem"] = Relationship(back_populates="location_links")
    location: Optional[Location] = Relationship(back_populates="poem_links")


# ---------------------------------------------------------------------------
# Poem
# ---------------------------------------------------------------------------

class PoemBase(SQLModel):
    title: str = Field(max_length=100)
    author_id: int = Field(foreign_key="poets.id")
    dynasty: str = Field(default="唐", max_length=10)
    content: str
    written_year: Optional[int] = None
    occasion: Optional[str] = None


class Poem(PoemBase, table=True):
    __tablename__ = "poems"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    author: Optional[Poet] = Relationship(back_populates="poems")
    location_links: list[PoemLocation] = Relationship(back_populates="poem")


class PoemRead(PoemBase):
    id: int


class PoemCreate(PoemBase):
    pass
