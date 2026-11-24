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


NO_CACHE = {"Cache-Control": "no-cache"}


def _is_asset_path(full_path: str) -> bool:
    return full_path == "assets" or full_path.startswith("assets/")


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    root = DIST_DIR.resolve()
    index = root / "index.html"
    if full_path:
        try:
            candidate = (root / full_path).resolve()
        except (ValueError, OSError):  # e.g. a null byte in the path
            candidate = None
        # Containment first: never touch a path outside the built app.
        if candidate is not None and candidate.is_relative_to(root) and candidate.is_file():
            if candidate == index:
                return FileResponse(index, headers=NO_CACHE)
            return FileResponse(candidate)
    # A missing built file is a real 404; serving the shell would hide a stale deploy.
    if _is_asset_path(full_path):
        raise HTTPException(status_code=404, detail="Not found")
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    # The shell names the hashed assets, so browsers must revalidate it.
    return FileResponse(index, headers=NO_CACHE)
