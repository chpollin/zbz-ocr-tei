"""Shared scaffolding for the reversible tei_final marker runs.

The E92/E94 marker tools (tei_char_normalize, tei_pb_folio, tei_body_note_demote,
tei_status_marker, tei_blank_marker) all rewrite output/tei_final/{doc}_final.xml as
reversible runs guarded by --dry-run and backed up before the write. Two pieces of
that scaffolding are genuinely common and live here so the tools do not each carry
their own copy.
"""

import shutil
from pathlib import Path

from scripts.config import TEI_FINAL_DIR


def iter_final_files(only_doc=None):
    """Yield (doc_id, path) for each output/tei_final/*_final.xml in sorted order.

    doc_id is the file name with the trailing "_final.xml" stripped. With only_doc
    set, only that document is yielded (nothing if it has no final TEI).
    """
    for path in sorted(TEI_FINAL_DIR.glob("*_final.xml")):
        doc_id = path.name[: -len("_final.xml")]
        if only_doc and doc_id != only_doc:
            continue
        yield doc_id, path


def backup_and_write(path: Path, backup_dir: Path, text: str) -> None:
    """Back up `path` into `backup_dir` (same file name), then overwrite it with `text`.

    The backup is the undo path for a real marker run; copy2 preserves the pre-state
    verbatim before the file is rewritten.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_dir / path.name)
    path.write_text(text, encoding="utf-8")
