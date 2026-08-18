import streamlit as st

import common

common.inject_css()
common.render_sidebar(active_title="Home")

common.eyebrow("HEBA")
common.display_heading("Reports")
common.qualifier("Select a site.")
common.header_rule()

st.page_link(common.TIROL_PAGE, label="Tirol — HeBA/Tirol/OSQ survey", width="stretch")
st.page_link(common.LUXEMBOURG_PAGE, label="Luxembourg — HeBA/Luxembourg/OSQ survey", width="stretch")
