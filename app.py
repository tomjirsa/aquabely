import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
/* Hide the Import nav item from the sidebar while keeping it routable via URL */
section[data-testid="stSidebar"] a[href$="import"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

pg = st.navigation([
    st.Page("pages/2_athlete.py", title="Athletes", icon="🏊", default=True),
    st.Page("pages/3_club.py", title="Clubs", icon="🏆"),
    st.Page("pages/4_competition.py", title="Competitions", icon="📋"),
    st.Page("pages/1_import.py", title="Import", icon="📥", url_path="import"),
])
pg.run()
