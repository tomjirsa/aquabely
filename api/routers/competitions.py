import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas import CompetitionEntry, FigureDetailRow, FigureRow, ResultRow
from api.services.scoring import trimmed_flags
from db import queries
from db.database import get_connection, init_schema

router = APIRouter(prefix="/api/competitions")

JUDGE_COLS = [f"judge_{i}" for i in range(1, 8)]


def records(df: pd.DataFrame) -> list[dict]:
    """DataFrame to list of dicts with NaN/NaT mapped to None."""
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def run(fn, *args):
    conn = get_connection()
    try:
        init_schema(conn)
        return fn(conn, *args)
    finally:
        conn.close()


def run_for_category(cc_id: int, fn):
    def inner(conn):
        exists = conn.execute(
            "SELECT 1 FROM competition_categories WHERE id = ?", (cc_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Competition not found")
        return fn(conn, cc_id)
    return run(inner)


@router.get("", response_model=list[CompetitionEntry])
def list_competitions(level: str):
    return records(run(queries.competitions_for_level, level))


@router.get("/{cc_id}/results", response_model=list[ResultRow])
def results(cc_id: int):
    return records(run_for_category(cc_id, queries.results_for))


@router.get("/{cc_id}/figures", response_model=list[FigureRow])
def figures(cc_id: int):
    return records(run_for_category(cc_id, queries.competition_figures))


@router.get("/{cc_id}/figure-detail", response_model=list[FigureDetailRow])
def figure_detail(cc_id: int):
    out = []
    for row in records(run_for_category(cc_id, queries.competition_figure_detail)):
        judges = [row.pop(c) for c in JUDGE_COLS]
        dropped, average = trimmed_flags(judges)
        out.append({**row, "judges": judges, "dropped": dropped, "average": average})
    return out
