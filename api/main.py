from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

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


LEGACY_PATHS = {"/Import": "/import", "/Competitions": "/competitions",
                "/Athletes": "/athletes", "/Clubs": "/clubs", "/Figures": "/figures"}


def _redirect_to(target: str):
    def redirect():
        return RedirectResponse(target, status_code=301)
    return redirect


# Registered before the SPA catch-all so the catch-all never swallows them.
for _old, _new in LEGACY_PATHS.items():
    app.add_api_route(_old, _redirect_to(_new), methods=["GET"], include_in_schema=False)


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    candidate = (DIST_DIR / full_path).resolve()
    if full_path and candidate.is_file() and candidate.is_relative_to(DIST_DIR.resolve()):
        return FileResponse(candidate)
    index = DIST_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(index)
