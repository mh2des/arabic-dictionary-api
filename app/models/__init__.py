"""
Pydantic data models for the Arabic dictionary backend.

These models define the complete structure of a lexical entry.  They are
loosely based on lexicographic standards but extended to support
multiple senses, examples, semantic relations, pronunciations,
dialectal variants, inflections and derivations.  A helper function
``schema()`` produces a JSON schema for validation.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class Morphology(BaseModel):
    """Morphological features for verbs and nouns."""

    form: Optional[str] = None
    voice: Optional[str] = None
    transitivity: Optional[str] = None
    valency: Optional[str] = None
    aspect: Optional[str] = None


class QualityMeta(BaseModel):
    """Metadata describing the quality/confidence of an entry."""

    reviewed: bool = False
    confidence: Optional[float] = None
    source_count: Optional[int] = None
    
    class Config:
        extra = "forbid"


class Info(BaseModel):
    """High‑level lexical information about a lemma."""

    lemma: str
    lemma_norm: str
    orthographic_variants: List[str] = Field(default_factory=list)
    root: Optional[str] = None
    pattern: Optional[str] = None
    pos: List[str] = Field(default_factory=list)
    subpos: Optional[str] = None
    morph: Optional[Morphology] = None
    # Verb helpers
    masdars: Optional[List[str]] = None
    active_participle: Optional[str] = None
    passive_participle: Optional[str] = None
    imperfect_stem: Optional[str] = None
    # Noun helpers
    gender: Optional[str] = None
    plurals: Optional[List[str]] = None
    diminutives: Optional[List[str]] = None
    nisba: Optional[List[str]] = None
    # Metadata
    register_: Optional[str] = Field(default=None, alias="register")
    domain: Optional[str] = None
    freq: Optional[Dict[str, Any]] = None
    etymology: Optional[str] = None
    quality: Optional[QualityMeta] = None
    updated_at: Optional[str] = None


class Sense(BaseModel):
    """A particular meaning of a lemma."""

    id: str
    gloss_ar_short: Optional[str] = None
    gloss_ar: Optional[str] = None
    gloss_en: Optional[str] = None
    labels: Optional[List[str]] = None
    domains: Optional[List[str]] = None
    usage_notes: Optional[str] = None
    subcat: Optional[str] = None
    synonyms_ar: Optional[List[str]] = None
    antonyms_ar: Optional[List[str]] = None
    hypernyms: Optional[List[str]] = None
    hyponyms: Optional[List[str]] = None
    translations: Optional[Dict[str, str]] = None
    confidence: Optional[float] = None


class Example(BaseModel):
    """Example sentence illustrating a sense or lemma."""

    ar: str
    en: Optional[str] = None
    dialect: Optional[str] = None
    register_: Optional[str] = Field(default=None, alias="register")
    audio: Optional[List[str]] = None
    source: Optional[str] = None
    license: Optional[str] = None
    highlight: Optional[List[int]] = None
    irab: Optional[str] = None


class RelationItem(BaseModel):
    """An individual semantic relation."""
    id: str
    sense: Optional[str] = None
    note: Optional[str] = None


class Relations(BaseModel):
    """Group of semantic relations for a lemma."""
    synonyms: Optional[List[RelationItem]] = None
    near_synonyms: Optional[List[RelationItem]] = None
    antonyms: Optional[List[RelationItem]] = None
    related: Optional[List[RelationItem]] = None


class PronFields(BaseModel):
    """Detailed pronunciation fields."""
    ipa: Optional[str] = None
    phonetic: Optional[str] = None
    syllables: Optional[str] = None
    stress: Optional[str] = None
    latin: Optional[str] = None
    audio: Optional[List[str]] = None
    tts_provider: Optional[str] = None
    quality: Optional[str] = None


class Pronunciation(BaseModel):
    """Pronunciation representation with transliteration and rhyme info."""
    pron: Optional[PronFields] = None
    translits: Optional[Dict[str, str]] = None
    rhyme_key: Optional[str] = None


class DialectVariant(BaseModel):
    """Representation of a lemma in a particular dialect."""
    dialect: str
    lemma: str
    pron: Optional[Pronunciation] = None
    senses: Optional[List[Sense]] = None
    examples: Optional[List[Example]] = None
    notes: Optional[str] = None
    equivalence: Optional[str] = None


class Inflection(BaseModel):
    """Inflection tables for verbs and nouns."""
    verb_tables: Optional[Dict[str, Dict[str, str]]] = None
    noun_tables: Optional[Dict[str, Any]] = None


class Derivations(BaseModel):
    """Derived forms related to a lemma."""
    masdars: Optional[List[str]] = None
    ism_fa3il: Optional[str] = None
    ism_maf3ul: Optional[str] = None
    sifah_mushabbaha: Optional[str] = None
    nouns_from_root: Optional[List[str]] = None


class Entry(BaseModel):
    """Complete structured lexical entry."""
    info: Info
    senses: Optional[List[Sense]] = None
    examples: Optional[List[Example]] = None
    relations: Optional[Relations] = None
    pronunciation: Optional[Pronunciation] = None
    dialects: Optional[List[DialectVariant]] = None
    inflection: Optional[Inflection] = None
    derivations: Optional[Derivations] = None

    class Config:
        allow_population_by_field_name = True


def schema() -> Dict[str, Any]:
    """Return the JSON Schema for an Entry."""
    return Entry.model_json_schema()
