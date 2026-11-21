import streamlit as st

from db.database import get_connection, init_schema
from db.queries import catalogue_figures
from ui.theme import inject_theme

inject_theme()
st.title("Figures")

conn = get_connection()
init_schema(conn)

level = st.radio("Level", ["L3", "U12"], horizontal=True)
figures = catalogue_figures(conn, level)
conn.close()

if figures.empty:
    st.info("No figures in the catalogue for this level.")
    st.stop()

if int(figures["performances"].sum()) == 0:
    st.info("No performances recorded yet. Use the Import page to add results.")

st.dataframe(
    figures[["code", "name", "coefficient", "description_cs", "performances", "competitions"]],
    hide_index=True,
    width="stretch",
)
