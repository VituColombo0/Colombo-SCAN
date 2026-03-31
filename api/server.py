"""
Colombo Scanner — REST API (FastAPI)
Provides programmatic access to the scanning engine.
Usage: python main.py --api
"""
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import APIKeyHeader
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.plugin_manager import load_plugins
from core.runner import run_plugins_paralelo
from core.smart_scan import filtrar_plugins_smart, detectar_tipo
from core.database import (
    create_case, list_cases, get_case, get_case_stats,
    create_scan, finish_scan, save_raw_result, save_entities,
    get_raw_results_by_scan, get_entities_by_case, get_entity_correlations
)
from core.intelligence import extrair_entidades
from core.logger import get_logger

log = get_logger("api")


def create_app():
    if not HAS_FASTAPI:
        raise ImportError("FastAPI não instalado. Execute: pip install fastapi uvicorn")

    API_KEY = os.environ.get("COLOMBO_API_KEY")
    if not API_KEY:
        import uuid
        API_KEY = str(uuid.uuid4())
        log.warning(f"COLOMBO_API_KEY não definida. Chave autogerada (Security by Default): {API_KEY}")

    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

    async def verify_api_key(api_key: str = Depends(api_key_header)):
        if api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Acesso negado: API Key inválida")

    app = FastAPI(
        title="Colombo Scanner API",
        description="API REST protegida e segura",
        version="4.2.0",
        dependencies=[Depends(verify_api_key)]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    plugins = load_plugins()

    # --- Models ---

    class ScanRequest(BaseModel):
        target: str = Field(..., min_length=1, max_length=2000, description="Alvo a ser escaneado")
        case_id: int | None = None
        category: str | None = Field(None, max_length=100)
        max_workers: int = Field(5, gt=0, le=20, description="Máximo de workers paralelos (1-20)")

    class CaseCreate(BaseModel):
        name: str
        description: str = ""

    # --- Routes ---

    @app.get("/")
    def root():
        return {
            "service": "Colombo Scanner API",
            "version": "4.2.0",
            "plugins_loaded": len(plugins)
        }

    @app.get("/plugins")
    def list_plugins_api():
        return [
            {
                "name": p.get("name"),
                "category": p.get("category"),
                "description": p.get("description", ""),
            }
            for p in plugins
        ]

    @app.get("/categories")
    def list_categories():
        cats = {}
        for p in plugins:
            cat = p.get("category", "Outros")
            cats.setdefault(cat, 0)
            cats[cat] += 1
        return cats

    @app.post("/scan")
    def run_scan(req: ScanRequest, background_tasks: BackgroundTasks):
        """Launch a scan. Returns scan_id for polling results."""
        target = req.target.strip()
        if not target:
            raise HTTPException(400, "Target is required")
        if req.max_workers <= 0:
            raise HTTPException(400, "max_workers must be greater than 0")
        if req.max_workers > 20:
            log.warning(f"Limitando max_workers de {req.max_workers} para 20.")
            req.max_workers = 20

        tipo = detectar_tipo(target)

        if req.category:
            selected = [p for p in plugins if p.get("category") == req.category]
        else:
            selected = filtrar_plugins_smart(plugins, target)

        if not selected:
            raise HTTPException(404, f"No plugins found for target type: {tipo}")

        case_id = req.case_id or create_case(f"API Scan: {target[:30]}")
        scan_id = create_scan(case_id, target, scan_type="api", plugin_count=len(selected))

        # Run scan in background
        def _background_scan():
            try:
                resultados = run_plugins_paralelo(selected, {"alvo": target}, max_workers=req.max_workers)
                all_entities = []
                for r in resultados:
                    save_raw_result(scan_id, r.plugin_name, target, r.raw_output)
                    ents = extrair_entidades(r.raw_output, r.plugin_name, target)
                    all_entities.extend(ents)
                if all_entities:
                    save_entities(case_id, scan_id, all_entities)
                finish_scan(scan_id, "completed")
                log.info(f"API scan {scan_id} concluído: {len(resultados)} plugins, {len(all_entities)} entidades")
            except Exception as e:
                finish_scan(scan_id, "error")
                log.error(f"API scan {scan_id} falhou: {e}")

        background_tasks.add_task(_background_scan)

        return {
            "scan_id": scan_id,
            "case_id": case_id,
            "target": target,
            "target_type": tipo,
            "plugins_selected": len(selected),
            "status": "running"
        }

    @app.get("/scan/{scan_id}/results")
    def get_results(scan_id: int, limit: int = 100, skip: int = 0):
        results = get_raw_results_by_scan(scan_id, limit=limit, offset=skip)
        if not results:
            raise HTTPException(404, "Scan not found or no results yet")
        return results

    # --- Case Routes ---

    @app.post("/cases")
    def create_case_api(req: CaseCreate):
        case_id = create_case(req.name, req.description)
        return {"id": case_id, "name": req.name}

    @app.get("/cases")
    def list_cases_api(status: str = "active", limit: int = 50, skip: int = 0):
        return list_cases(status, limit=limit, offset=skip)

    @app.get("/cases/{case_id}")
    def get_case_api(case_id: int):
        case = get_case(case_id)
        if not case:
            raise HTTPException(404, "Case not found")
        stats = get_case_stats(case_id)
        return {**case, "stats": stats}

    @app.get("/cases/{case_id}/entities")
    def get_case_entities(case_id: int, limit: int = 200, skip: int = 0):
        return get_entities_by_case(case_id, limit=limit, offset=skip)

    @app.get("/cases/{case_id}/correlations")
    def get_case_correlations(case_id: int):
        return get_entity_correlations(case_id)

    @app.get("/cases/{case_id}/scans")
    def list_case_scans(case_id: int, limit: int = 50, skip: int = 0):
        from core.database import get_connection
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM scans WHERE case_id = ? ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (case_id, limit, skip)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return app


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """Starts the API server."""
    import uvicorn
    app = create_app()
    log.info(f"API iniciando em http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
