import streamlit as st

import common

st.set_page_config(page_title="HeBA Reports", layout="centered")

pg = st.navigation(common.PAGES, position="hidden")
pg.run()
