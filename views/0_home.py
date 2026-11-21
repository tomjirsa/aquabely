import streamlit as st

from db.database import get_connection, init_schema
from db.queries import competitions_for_level, level_athlete_count, results_for
from ui.components import stat_card
from ui.theme import inject_theme

inject_theme()
st.title("Aquabely")

conn = get_connection()
init_schema(conn)

LEVELS = ["L3", "U12"]


def level_summary(level):
    comps = competitions_for_level(conn, level)
    if comps.empty:
        return None
    latest = comps.sort_values(["date", "competition_category_id"]).iloc[-1]
    n_athletes = level_athlete_count(conn, level)
    res = results_for(conn, int(latest["competition_category_id"]))
    top = None
    ranked = res.dropna(subset=["rank"])
    if not ranked.empty:
        row = ranked.sort_values("rank").iloc[0]
        top = f"{row['name']} ({row['total_score']:.2f})"
    return {"competition": f"{latest['competition']} ({latest['date']})",
            "athletes": str(n_athletes), "top": top or "n/a",
            "age_group": str(latest["age_group_label"])}


summaries = {lvl: level_summary(lvl) for lvl in LEVELS}

if all(s is None for s in summaries.values()):
    st.info("No results yet. Use the Import page to add a results PDF.")
else:
    choice = st.radio("Level", LEVELS, horizontal=True)
    s = summaries[choice]
    st.subheader(choice)
    if s is None:
        st.caption(f"No {choice} competitions imported yet.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            stat_card("Latest competition", s["competition"])
        with c2:
            stat_card("Athletes", s["athletes"])
        with c3:
            stat_card("Top placing (" + s["age_group"] + ")", s["top"])
conn.close()
