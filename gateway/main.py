"""LineLock gateway. Phase 2: guardrails, claim amount, approval, pitch recordings."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import amount
import extract
import guardrails
import llm
import rules
import workflow

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("linelock")

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "data" / "library"
PACKETS = ROOT / "data" / "packets"
UPLOADS = ROOT / "data" / "uploads"
PITCH = ROOT / "data" / "pitch" / "runs.json"
DB_PATH = ROOT / "linelock.db"
UPLOADS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="LineLock gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

FILES = [
    "po.pdf",
    "drawing.pdf",
    "drawing.json",
    "delivery_note.pdf",
    "material_cert.pdf",
    "supplier_report.pdf",
    "cmm_report.pdf",
    "calibration.json",
]


class Approval(BaseModel):
    action: str
    reason: str = ""


class Edit(BaseModel):
    characteristic_id: str
    measured: float


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder TEXT NOT NULL,
            disposition TEXT NOT NULL,
            record_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def _audit(conn: sqlite3.Connection, case_id: int, event: str, detail: dict) -> None:
    conn.execute(
        "INSERT INTO audit (case_id, event, detail) VALUES (?, ?, ?)",
        (case_id, event, json.dumps(detail)),
    )
    log.info("step=audit case=%s event=%s", case_id, event)


def _library_text() -> str:
    return "\n\n".join(path.read_text() for path in sorted(LIBRARY.glob("*.md")))


def run_case(folder: Path) -> dict:
    log.info("step=extract folder=%s", folder.name)
    extractions = extract.extract_packet(folder)
    drawing = json.loads((folder / "drawing.json").read_text())
    ordered = next(
        item["fields"]["drawing_revision"]["value"]
        for item in extractions
        if item["document"] == "po"
    )
    log.info("step=map model_call=chat/completions revision=%s", ordered)
    mapping = llm.map_features(drawing["revisions"][ordered], extractions)
    conformance = rules.evaluate(drawing, extractions, mapping)
    log.info("step=rules disposition=%s reasons=%s", conformance["disposition"], conformance["reasons"])

    decision = None
    notes: list[str] = []
    if conformance["disposition"] != "release":
        log.info("step=decide model_call=chat/completions")
        decision = llm.decide(conformance, _library_text())
        decision, notes = guardrails.apply(decision, LIBRARY)
        log.info("step=guardrail responsibility=%s notes=%s", decision.get("responsibility"), notes)

    claim = amount.claim_amount(extractions, decision, LIBRARY)
    log.info("step=amount eur=%s", claim)
    translated = ""
    if decision and decision.get("responsibility") == "supplier":
        language = "de"
        for item in extractions:
            if item["document"] == "supplier_report" and "language" in item["fields"]:
                language = item["fields"]["language"]["value"]
        source = decision.get("supplier_email") or decision.get("ncr_text") or ""
        log.info("step=translate language=%s", language)
        try:
            translated = llm.translate(source, language)
        except httpx.HTTPError:
            log.info("step=translate fallback=model")
            saved = os.environ.get("TRANSLATE_BACKEND")
            os.environ["TRANSLATE_BACKEND"] = "local"
            try:
                translated = llm.translate(source, language)
            finally:
                if saved is None:
                    os.environ.pop("TRANSLATE_BACKEND", None)
                else:
                    os.environ["TRANSLATE_BACKEND"] = saved
    return {
        "extractions": extractions,
        "mapping": mapping,
        "conformance": conformance,
        "decision": decision,
        "guardrail": notes,
        "amount": claim,
        "supplier_email_translated": translated,
        "approval": None,
    }


def _save(conn, case_id: int, folder: Path, record: dict) -> None:
    disposition = record["conformance"]["disposition"]
    started = workflow.start_ncr(case_id, disposition, record["decision"], record["amount"])
    record["workflow"] = started
    log.info("step=workflow execution=%s target=%s", started["execution_id"], started["target"])
    conn.execute(
        "UPDATE cases SET folder=?, disposition=?, record_json=? WHERE id=?",
        (str(folder), disposition, json.dumps(record), case_id),
    )
    _audit(conn, case_id, "created", {"disposition": disposition, "amount": record["amount"], "guardrail": record["guardrail"]})


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "model": os.environ.get("LLM_BASE_URL", ""),
        "extractor": os.environ.get("EXTRACTOR", "local"),
        "translate": os.environ.get("TRANSLATE_BACKEND", "local"),
        "evolus_workflow": bool(os.environ.get("EVOLUS_WORKFLOW_ID", "").strip()),
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "static" / "index.html").read_text()


@app.get("/cases")
def list_cases() -> list[dict]:
    rows = _db().execute("SELECT id, disposition, record_json, created_at FROM cases ORDER BY id DESC").fetchall()
    result = []
    for row in rows:
        record = json.loads(row["record_json"] or "{}")
        result.append(
            {
                "id": row["id"],
                "disposition": row["disposition"],
                "amount": record.get("amount"),
                "responsibility": (record.get("decision") or {}).get("responsibility"),
                "approval": record.get("approval"),
                "created_at": row["created_at"],
            }
        )
    return result


@app.post("/packets")
async def create_packet(files: list[UploadFile] = File(...)) -> dict:
    names = {item.filename for item in files}
    missing = [name for name in FILES if name not in names]
    if missing:
        raise HTTPException(400, f"missing files: {missing}")
    conn = _db()
    case_id = conn.execute("INSERT INTO cases (folder, disposition, record_json) VALUES ('', '', '{}')").lastrowid
    folder = UPLOADS / f"case-{case_id}"
    folder.mkdir(parents=True, exist_ok=True)
    for item in files:
        with (folder / item.filename).open("wb") as handle:
            shutil.copyfileobj(item.file, handle)
    try:
        record = run_case(folder)
    except Exception as exc:
        log.exception("step=failed case=%s", case_id)
        raise HTTPException(502, str(exc)) from exc
    _save(conn, case_id, folder, record)
    conn.commit()
    return {"id": case_id, "disposition": record["conformance"]["disposition"], "record": record}


@app.get("/cases/{case_id}")
def get_case(case_id: int) -> dict:
    conn = _db()
    row = conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "not found")
    audit = conn.execute("SELECT event, detail, created_at FROM audit WHERE case_id=? ORDER BY id", (case_id,)).fetchall()
    return {
        "id": row["id"],
        "disposition": row["disposition"],
        "record": json.loads(row["record_json"]),
        "audit": [{"event": item["event"], "detail": json.loads(item["detail"]), "created_at": item["created_at"]} for item in audit],
    }


@app.post("/cases/{case_id}/approve")
def approve(case_id: int, body: Approval) -> dict:
    if body.action not in {"approve_claim", "release_concession"}:
        raise HTTPException(400, "unknown action")
    if body.action == "release_concession" and not body.reason.strip():
        raise HTTPException(400, "a concession needs a reason")
    conn = _db()
    row = conn.execute("SELECT record_json, disposition FROM cases WHERE id=?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "not found")
    record = json.loads(row["record_json"])
    if body.action == "approve_claim" and (record.get("decision") or {}).get("responsibility") != "supplier":
        raise HTTPException(400, "there is no supplier claim to approve")
    if body.action == "release_concession" and row["disposition"] == "release":
        raise HTTPException(400, "this batch is already released")
    record["approval"] = {"action": body.action, "reason": body.reason.strip()}
    conn.execute("UPDATE cases SET record_json=? WHERE id=?", (json.dumps(record), case_id))
    _audit(conn, case_id, body.action, record["approval"])
    conn.commit()
    return get_case(case_id)


@app.post("/cases/{case_id}/edit")
def edit_case(case_id: int, body: Edit) -> dict:
    conn = _db()
    row = conn.execute("SELECT folder, record_json FROM cases WHERE id=?", (case_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "not found")
    folder = Path(row["folder"])
    previous = json.loads(row["record_json"])
    mapping = json.loads(json.dumps(previous["mapping"]))
    changed = False
    for row_map in mapping:
        if row_map["characteristic_id"] == body.characteristic_id and row_map["source_document"] == "cmm_report":
            row_map["measured_value"] = body.measured
            changed = True
    if not changed:
        raise HTTPException(400, "that characteristic is not on the CMM report")
    drawing = json.loads((folder / "drawing.json").read_text())
    conformance = rules.evaluate(drawing, previous["extractions"], mapping)
    decision = None
    notes: list[str] = []
    if conformance["disposition"] != "release":
        decision = llm.decide(conformance, _library_text())
        decision, notes = guardrails.apply(decision, LIBRARY)
    claim = amount.claim_amount(previous["extractions"], decision, LIBRARY)
    record = {
        "extractions": previous["extractions"],
        "mapping": mapping,
        "conformance": conformance,
        "decision": decision,
        "guardrail": notes,
        "amount": claim,
        "supplier_email_translated": previous.get("supplier_email_translated", ""),
        "approval": None,
        "edited": {"characteristic_id": body.characteristic_id, "measured": body.measured},
    }
    _save(conn, case_id, folder, record)
    conn.commit()
    log.info("step=edit case=%s %s=%s disposition=%s", case_id, body.characteristic_id, body.measured, conformance["disposition"])
    return get_case(case_id)


@app.post("/pitch/record")
def record_pitch() -> dict:
    conn = _db()
    runs = []
    for name in ("P01", "P06", "P09", "P11"):
        folder = PACKETS / name
        case_id = conn.execute("INSERT INTO cases (folder, disposition, record_json) VALUES ('', '', '{}')").lastrowid
        record = run_case(folder)
        _save(conn, case_id, folder, record)
        runs.append({"packet": name, "id": case_id, "disposition": record["conformance"]["disposition"], "record": record})
    conn.commit()
    PITCH.parent.mkdir(parents=True, exist_ok=True)
    PITCH.write_text(json.dumps(runs))
    log.info("step=pitch recorded=%s", [item["packet"] for item in runs])
    return {"packets": [item["packet"] for item in runs]}


@app.get("/pitch")
def pitch() -> dict:
    if not PITCH.is_file():
        raise HTTPException(404, "no recording yet")
    return {"label": "Recording of a live run. Not a new model call.", "runs": json.loads(PITCH.read_text())}
