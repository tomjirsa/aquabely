import streamlit as st

st.set_page_config(layout="wide")
st.markdown('<style>section[data-testid="stSidebar"] a[href$="import"]{display:none !important}</style>', unsafe_allow_html=True)

pg = st.navigation([
    st.Page("views/0_home.py", title="Home", icon="🏠", default=True),
    st.Page("views/2_competitions.py", title="Competitions", icon="📋"),
    st.Page("views/3_athletes.py", title="Athletes", icon="🏊"),
    st.Page("views/4_clubs.py", title="Clubs", icon="🏆"),
    st.Page("views/1_import.py", title="Import", icon="📥", url_path="import"),
])
pg.run()
