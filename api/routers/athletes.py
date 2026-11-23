import pandas as pd
from fastapi import APIRouter, HTTPException

from api.routers.competitions import JUDGE_COLS, records, run
from api.schemas import AthleteCompetition, AthleteProfile, AthleteSummary, FigureHistory
from api.services.scoring import trimmed_flags
from db import queries

router = APIRouter(prefix="/api/athletes")

FIG_RANK_COLS = ["fig_rank_overall", "fig_rank_by_year", "fig_field_size", "fig_field_size_by_year"]
RANK_KEYS = ["rank_overall", "rank_by_year", "field_size", "field_size_by_year"]


def summaries(conn) -> pd.DataFrame:
    return queries.athlete_list(conn).merge(queries.athlete_summaries(conn), on="id")


def run_for_athlete(athlete_id: int, fn):
    def inner(conn):
        exists = conn.execute("SELECT 1 FROM athletes WHERE id = ?", (athlete_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Athlete not found")
        return fn(conn, athlete_id)
    return run(inner)


def with_trimmed(row: dict) -> dict:
    judges = [row.pop(c) for c in JUDGE_COLS]
    dropped, average = trimmed_flags(judges)
    return {**row, "judges": judges, "dropped": dropped, "average": average}


@router.get("", response_model=list[AthleteSummary])
def list_athletes(q: str = ""):
    df = run(summaries)
    query = q.strip().lower()
    if query:
        df = df[df["name"].str.lower().str.contains(query, regex=False)
                | df["club"].str.lower().str.contains(query, regex=False)]
    return records(df.drop(columns=["country"]))


def _profile(conn, athlete_id):
    df = summaries(conn)
    summary = records(df[df["id"] == athlete_id].drop(columns=["country"]))[0]
    history = queries.athlete_history(conn, athlete_id).drop(
        columns=["result_id", "competition_category_id"])
    return {**summary, "history": records(history),
            "overall_ranks": records(queries.athlete_overall_ranks(conn, athlete_id))}


@router.get("/{athlete_id}", response_model=AthleteProfile)
def profile(athlete_id: int):
    return run_for_athlete(athlete_id, _profile)


def _competitions(conn, athlete_id):
    history = queries.athlete_history(conn, athlete_id)
    rank_df = queries.athlete_rankings(conn, athlete_id)
    detail = queries.athlete_figure_detail(conn, athlete_id)

    cols = ["competition", "date", "figure_name", *FIG_RANK_COLS]
    fig_ranks = (rank_df[cols].drop_duplicates(["competition", "date", "figure_name"])
                 if not rank_df.empty else pd.DataFrame(columns=cols))
    merged = detail.merge(fig_ranks, on=["competition", "date", "figure_name"], how="left")

    out = []
    for date, name in dict.fromkeys(zip(history["date"], history["competition"])):
        rank_row = rank_df[(rank_df["competition"] == name) & (rank_df["date"] == date)]
        if rank_row.empty:
            past = history[(history["competition"] == name) & (history["date"] == date)].iloc[0]
            ranks = {"rank_overall": past["rank"], "rank_by_year": None,
                     "field_size": past["field_size"], "field_size_by_year": None}
        else:
            ranks = {k: rank_row[k].iloc[0] for k in RANK_KEYS}
        comp_fig = merged[(merged["competition"] == name) & (merged["date"] == date)]
        figures = [with_trimmed({k: v for k, v in row.items() if k not in ("competition", "date")})
                   for row in records(comp_fig)]
        out.append({"date": date, "competition": name,
                    **records(pd.DataFrame([ranks]))[0], "figures": figures})
    return out


@router.get("/{athlete_id}/competitions", response_model=list[AthleteCompetition])
def competitions(athlete_id: int):
    return run_for_athlete(athlete_id, _competitions)


def _figures(conn, athlete_id):
    detail = queries.athlete_figure_detail(conn, athlete_id)
    out: dict = {}
    for row in records(detail):
        point = with_trimmed(row)
        name = point.pop("figure_name")
        point.pop("coefficient")
        out.setdefault(name, []).append(point)
    return [{"figure_name": n, "points": pts} for n, pts in out.items()]


@router.get("/{athlete_id}/figures", response_model=list[FigureHistory])
def figures(athlete_id: int):
    return run_for_athlete(athlete_id, _figures)
