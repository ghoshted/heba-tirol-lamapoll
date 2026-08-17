import datetime

import streamlit as st

import common

common.require_password("luxembourg", "Luxembourg")

common.inject_css()
common.render_sidebar(active_title="Luxembourg", auth_key="luxembourg")

common.eyebrow("HEBA-LUXEMBOURG")
common.display_heading("Site: Luxembourg")
today = datetime.date.today()
common.qualifier(f"updated {today.day:02d}·{today.month:02d}·{today.year % 100:02d}")
common.header_rule()

lama_api_key = st.secrets["lamapoll_api_key"]
poll_id = 2103465

df = common.fetch_participants_df(lama_api_key, poll_id)
common.render_participant_figures(df)

df_devices = common.fetch_devices_df(lama_api_key, poll_id)
common.render_devices_figure(df_devices)
