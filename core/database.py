"""
Colombo Scanner — SQLite Database for Persistence
Stores cases, scans, entities, relations, and raw results.
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional
from core.logger import get_logger
from core.entities import Entity, EntityType, Relation, RelationType

log = get_logger("database")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "colombo.db")


def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Creates all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            target TEXT NOT NULL,
            scan_type TEXT DEFAULT 'direct',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            plugin_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            FOREIGN KEY (case_id) REFERENCES cases(id)
        );

        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            scan_id INTEGER,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            source_tool TEXT DEFAULT '',
            source_target TEXT DEFAULT '',
            confidence REAL DEFAULT 1.0,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases(id),
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        );

        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            entity_a_value TEXT NOT NULL,
            entity_b_value TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            source_tool TEXT DEFAULT '',
            confidence REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        );

        CREATE TABLE IF NOT EXISTS raw_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            plugin_name TEXT NOT NULL,
            target TEXT NOT NULL,
            output TEXT DEFAULT '',
            status TEXT DEFAULT 'success',
            execution_time REAL DEFAULT 0.0,
            layer INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        );

        CREATE INDEX IF NOT EXISTS idx_entities_case ON entities(case_id);
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(value);
        CREATE INDEX IF NOT EXISTS idx_raw_results_scan ON raw_results(scan_id);
    """)
    conn.commit()
    conn.close()
    log.info("Database inicializado com sucesso")


# --- Case Operations ---

def create_case(name: str, description: str = "") -> int:
    """Creates a new investigation case. Returns case ID."""
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO cases (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (name, description, now, now)
    )
    case_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log.info(f"Case criado: #{case_id} '{name}'")
    return case_id


def list_cases(status: str = "active") -> list[dict]:
    """Lists all cases with optional status filter."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM cases WHERE status = ? ORDER BY updated_at DESC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_case(case_id: int) -> Optional[dict]:
    """Gets a specific case by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def close_case(case_id: int):
    """Marks a case as closed."""
    conn = get_connection()
    conn.execute(
        "UPDATE cases SET status = 'closed', updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), case_id)
    )
    conn.commit()
    conn.close()


def delete_case(case_id: int):
    """Deletes a case and all its associated data."""
    conn = get_connection()
    # Delete child records first to avoid foreign key violations
    conn.execute("DELETE FROM raw_results WHERE scan_id IN (SELECT id FROM scans WHERE case_id = ?)", (case_id,))
    conn.execute("DELETE FROM entities WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM relations WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM scans WHERE case_id = ?", (case_id,))
    conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    conn.close()
    log.info(f"Case deletado: #{case_id}")


# --- Scan Operations ---

def create_scan(case_id: int, target: str, scan_type: str = "direct", plugin_count: int = 0) -> int:
    """Creates a new scan record. Returns scan ID."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO scans (case_id, target, scan_type, started_at, plugin_count) VALUES (?, ?, ?, ?, ?)",
        (case_id, target, scan_type, datetime.now().isoformat(), plugin_count)
    )
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id


def finish_scan(scan_id: int, status: str = "completed"):
    """Marks a scan as finished."""
    conn = get_connection()
    conn.execute(
        "UPDATE scans SET finished_at = ?, status = ? WHERE id = ?",
        (datetime.now().isoformat(), status, scan_id)
    )
    conn.commit()
    conn.close()


# --- Entity Operations ---

def save_entities(case_id: int, scan_id: int, entities: list[Entity]):
    """Batch inserts entities into the database."""
    if not entities:
        return

    conn = get_connection()
    now = datetime.now().isoformat()
    data = [
        (case_id, scan_id, e.type.value, e.value, e.source_tool,
         e.source_target, e.confidence, json.dumps(e.metadata), now)
        for e in entities
    ]
    
    # SQLite has a max variable limit (often 999 or 32766). We chunk inserts to prevent OperationalError.
    chunk_size = 500
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        conn.executemany(
            "INSERT INTO entities (case_id, scan_id, type, value, source_tool, source_target, confidence, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            chunk
        )
    conn.commit()
    conn.close()
    log.info(f"Salvos {len(entities)} entidades no case #{case_id}")


def get_entities_by_case(case_id: int) -> list[dict]:
    """Gets all entities for a case."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM entities WHERE case_id = ? ORDER BY created_at",
        (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_entity_correlations(case_id: int) -> list[dict]:
    """
    Finds entities that appear across multiple tools/scans.
    Returns entities with their occurrence count (correlation score).
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT value, type, COUNT(DISTINCT source_tool) as tool_count,
               GROUP_CONCAT(DISTINCT source_tool) as tools,
               COUNT(*) as total_occurrences
        FROM entities
        WHERE case_id = ?
        GROUP BY value, type
        HAVING tool_count > 1
        ORDER BY tool_count DESC
    """, (case_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_new_entities_diff(case_id: int, current_scan_id: int) -> list[dict]:
    """
    Finds entities from current_scan_id that did NOT exist in any PREVIOUS scans
    for the same case_id based on their (value, type) combination.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT e1.* FROM entities e1
        WHERE e1.scan_id = ?
        AND NOT EXISTS (
            SELECT 1 FROM entities e2
            WHERE e2.case_id = e1.case_id 
              AND e2.scan_id < e1.scan_id
              AND e2.value = e1.value 
              AND e2.type = e1.type
        )
    """, (current_scan_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Relation Operations ---

def save_relations(case_id: int, relations: list[Relation]):
    """Batch inserts relations into the database."""
    if not relations:
        return

    conn = get_connection()
    now = datetime.now().isoformat()
    data = [
        (case_id, r.entity_a_value, r.entity_b_value, r.relation_type.value,
         r.source_tool, r.confidence, now)
        for r in relations
    ]
    
    chunk_size = 500
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        conn.executemany(
            "INSERT INTO relations (case_id, entity_a_value, entity_b_value, relation_type, source_tool, confidence, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            chunk
        )
    conn.commit()
    conn.close()


# --- Raw Result Operations ---

def save_raw_result(scan_id: int, plugin_name: str, target: str, output: str,
                    status: str = "success", execution_time: float = 0.0, layer: int = 1):
    """Saves a raw plugin result."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO raw_results (scan_id, plugin_name, target, output, status, execution_time, layer, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (scan_id, plugin_name, target, output, status, execution_time, layer, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_raw_results_by_scan(scan_id: int) -> list[dict]:
    """Gets all raw results for a scan."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM raw_results WHERE scan_id = ? ORDER BY created_at",
        (scan_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_raw_results_by_case(case_id: int) -> list[dict]:
    """Recupera todos os resultados cruzados na linha do tempo para gerar Dossiês unindo múltiplas varreduras."""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT r.* FROM raw_results r 
           JOIN scans s ON r.scan_id = s.id 
           WHERE s.case_id = ? 
           ORDER BY r.created_at''',
        (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def check_cache_result(plugin_name: str, target: str, hours: int = 24) -> Optional[dict]:
    """Verifica se um resultado de sucesso já existe no banco para o plugin/alvo nas últimas N horas."""
    if not isinstance(hours, int) or hours <= 0:
        hours = 24
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM raw_results WHERE plugin_name = ? AND target = ? AND status = 'success' AND created_at >= datetime('now', ? || ' hours') ORDER BY created_at DESC LIMIT 1",
        (plugin_name, target, f"-{hours}")
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# --- Stats ---

def get_case_stats(case_id: int) -> dict:
    """Gets summary statistics for a case."""
    conn = get_connection()

    scan_count = conn.execute(
        "SELECT COUNT(*) FROM scans WHERE case_id = ?", (case_id,)
    ).fetchone()[0]

    entity_count = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE case_id = ?", (case_id,)
    ).fetchone()[0]

    entity_types = conn.execute(
        "SELECT type, COUNT(*) as cnt FROM entities WHERE case_id = ? GROUP BY type ORDER BY cnt DESC",
        (case_id,)
    ).fetchall()

    conn.close()

    return {
        "scan_count": scan_count,
        "entity_count": entity_count,
        "entity_types": {row["type"]: row["cnt"] for row in entity_types}
    }


# Initialize on import
init_db()
