from fastapi import APIRouter, HTTPException

from api.routers.competitions import records, run
from api.schemas import ClubDetail, ClubSummary
from db import queries

router = APIRouter(prefix="/api/clubs")


@router.get("", response_model=list[ClubSummary])
def list_clubs():
    return records(run(queries.club_list))


def _detail(conn, club_id):
    row = conn.execute("SELECT name FROM clubs WHERE id = ?", (club_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Club not found")
    return {"name": row[0],
            "roster": records(queries.club_roster(conn, club_id)),
            "medals": records(queries.club_medals(conn, club_id)),
            "avg_scores": records(queries.club_avg_scores(conn, club_id))}


@router.get("/{club_id}", response_model=ClubDetail)
def club_detail(club_id: int):
    return run(lambda conn: _detail(conn, club_id))
