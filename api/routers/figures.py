from typing import Literal

from fastapi import APIRouter

from api.routers.competitions import records, run
from api.schemas import CatalogueFigure
from db import queries

router = APIRouter(prefix="/api/figures")


@router.get("", response_model=list[CatalogueFigure])
def list_figures(level: Literal["L3", "U12"]):
    return records(run(lambda conn: queries.catalogue_figures(conn, level)))
