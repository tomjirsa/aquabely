from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from api.routers import athletes, clubs, competitions, figures, home, imports

DIST_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"

app = FastAPI(title="Aquabely API")
app.include_router(home.router)
app.include_router(competitions.router)
app.include_router(athletes.router)
app.include_router(figures.router)
app.include_router(clubs.router)
app.include_router(imports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index = DIST_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(index)
