from fastapi import APIRouter

from api.routers.competitions import records, run
from api.schemas import HomeSummary
from db import queries

router = APIRouter(prefix="/api")


def _summary(conn, level):
    comps = queries.competitions_for_level(conn, level)
    latest = records(comps.tail(1))[0] if len(comps) else None
    count = queries.level_athlete_count(conn, level)
    name = total = None
    if latest:
        res = records(queries.results_for(conn, latest["competition_category_id"]))
        scored = [r for r in res if r["total_score"] is not None]
        if scored:
            top = max(scored, key=lambda r: r["total_score"])
            name, total = top["name"], top["total_score"]
    return {"level": level, "latest_competition": latest, "athlete_count": count,
            "top_scorer_name": name, "top_scorer_total": total}


@router.get("/home", response_model=HomeSummary)
def home(level: str):
    return run(_summary, level)
