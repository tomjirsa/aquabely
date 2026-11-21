import streamlit as st

st.set_page_config(layout="wide")

pg = st.navigation([
    st.Page("pages/0_home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/2_competitions.py", title="Competitions", icon="📋"),
    st.Page("pages/3_athletes.py", title="Athletes", icon="🏊"),
    st.Page("pages/4_clubs.py", title="Clubs", icon="🏆"),
    st.Page("pages/1_import.py", title="Import", icon="📥", url_path="import"),
])
pg.run()
