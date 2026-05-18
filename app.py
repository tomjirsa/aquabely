import streamlit as st

pg = st.navigation([
    st.Page("pages/1_import.py", title="Import", icon="📥"),
    st.Page("pages/2_athlete.py", title="Athletes", icon="🏊"),
    st.Page("pages/3_club.py", title="Clubs", icon="🏆"),
    st.Page("pages/4_competition.py", title="Competitions", icon="📋"),
])
pg.run()
