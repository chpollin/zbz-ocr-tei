"""
Entity Store: Per-Dokument Entity Registry mit JSON-Persistenz.

Aggregiert NER-Ergebnisse (pro Seite) zu einem deduplizierten
Dokument-Level Store. Basis fuer Wikidata Reconciliation und TEI Injection.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from scripts.config import ENTITIES_DIR, KNOWN_ENTITIES, NER_ENTITY_TYPES


@dataclass
class EntityRecord:
    """Einzelner Entity-Eintrag im Store."""

    normalized: str
    entity_type: str  # person, organization, place, work, event, date
    surfaces: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    count: int = 0
    contexts: list[str] = field(default_factory=list)
    wikidata_qid: str | None = None
    wikidata_label: str | None = None
    wikidata_description: str | None = None
    confidence: float = 0.0
    gnd_id: str | None = None

    @property
    def key(self) -> str:
        return f"{self.entity_type}:{self.normalized.lower()}"

    @property
    def is_resolved(self) -> bool:
        return self.wikidata_qid is not None

    def ref_value(self) -> str:
        """TEI ref-Attribut Wert."""
        if self.wikidata_qid:
            return f"WD:{self.wikidata_qid}"
        if self.gnd_id:
            return self.gnd_id  # already "GND:..."
        return "WD:unknown"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EntityRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class EntityStore:
    """In-Memory Entity Registry mit JSON-Persistenz."""

    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.entities: dict[str, EntityRecord] = {}

    def add_page_entities(self, page: int, entities: list[dict]) -> None:
        """Fuegt Entities einer Seite hinzu, dedupliziert nach normalized+type."""
        for ent in entities:
            entity_type = ent.get("type", "")
            if entity_type not in NER_ENTITY_TYPES:
                continue

            normalized = ent.get("normalized", ent.get("surface", "")).strip()
            if not normalized:
                continue

            key = f"{entity_type}:{normalized.lower()}"
            surface = ent.get("surface", normalized).strip()
            context = ent.get("context", "").strip()

            if key in self.entities:
                rec = self.entities[key]
                rec.count += 1
                if surface not in rec.surfaces:
                    rec.surfaces.append(surface)
                if page not in rec.pages:
                    rec.pages.append(page)
                if context and context not in rec.contexts and len(rec.contexts) < 3:
                    rec.contexts.append(context)
            else:
                self.entities[key] = EntityRecord(
                    normalized=normalized,
                    entity_type=entity_type,
                    surfaces=[surface],
                    pages=[page],
                    count=1,
                    contexts=[context] if context else [],
                )

    def apply_seed_entities(self) -> int:
        """Matcht gegen KNOWN_ENTITIES aus config.py, setzt gnd_id.

        Returns:
            Anzahl gematchter Entities.
        """
        matched = 0
        for key, rec in self.entities.items():
            if rec.entity_type != "person":
                continue
            for name, gnd_ref in KNOWN_ENTITIES.items():
                if rec.normalized.lower() == name.lower():
                    rec.gnd_id = gnd_ref
                    matched += 1
                    break
                # Auch partielle Matches (Nachname)
                if name.lower() in rec.normalized.lower():
                    rec.gnd_id = gnd_ref
                    matched += 1
                    break
        return matched

    def get_unresolved(self) -> list[EntityRecord]:
        """Entities ohne Wikidata QID."""
        return [r for r in self.entities.values() if not r.is_resolved]

    def get_resolved(self) -> list[EntityRecord]:
        """Entities mit Wikidata QID."""
        return [r for r in self.entities.values() if r.is_resolved]

    def get_by_type(self, entity_type: str) -> list[EntityRecord]:
        """Alle Entities eines Typs."""
        return [r for r in self.entities.values() if r.entity_type == entity_type]

    def get_page_entities(self, page: int) -> list[EntityRecord]:
        """Alle Entities die auf einer bestimmten Seite vorkommen."""
        return [r for r in self.entities.values() if page in r.pages]

    def summary(self) -> dict:
        """Zusammenfassung: Counts by Type, resolved/unresolved."""
        by_type = {}
        for t in NER_ENTITY_TYPES:
            ents = self.get_by_type(t)
            by_type[t] = {
                "total": len(ents),
                "mentions": sum(e.count for e in ents),
                "resolved": sum(1 for e in ents if e.is_resolved),
            }
        total = len(self.entities)
        resolved = sum(1 for e in self.entities.values() if e.is_resolved)
        return {
            "doc_id": self.doc_id,
            "total_entities": total,
            "total_mentions": sum(e.count for e in self.entities.values()),
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": round(resolved / total, 3) if total > 0 else 0,
            "by_type": by_type,
        }

    # -- Persistenz --

    def to_json(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "summary": self.summary(),
        }

    @classmethod
    def from_json(cls, data: dict) -> "EntityStore":
        store = cls(data["doc_id"])
        for key, ent_data in data.get("entities", {}).items():
            store.entities[key] = EntityRecord.from_dict(ent_data)
        return store

    def save(self, path: Path | None = None) -> Path:
        """Speichert den Store als JSON."""
        if path is None:
            doc_dir = ENTITIES_DIR / self.doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            path = doc_dir / f"{self.doc_id}_entities.json"
        path.write_text(
            json.dumps(self.to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, doc_id: str, path: Path | None = None) -> "EntityStore":
        """Laedt einen gespeicherten Store."""
        if path is None:
            path = ENTITIES_DIR / doc_id / f"{doc_id}_entities.json"
        if not path.exists():
            return cls(doc_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_json(data)
