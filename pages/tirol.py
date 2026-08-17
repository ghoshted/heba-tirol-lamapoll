import datetime

import streamlit as st

import common

common.require_password("tirol", "Tirol")

common.inject_css()
common.render_sidebar(active_title="Tirol", auth_key="tirol")

common.eyebrow("HEBA-TIROL")
common.display_heading("Site: Tirol")
today = datetime.date.today()
common.qualifier(f"updated {today.day:02d}·{today.month:02d}·{today.year % 100:02d}")
common.header_rule()

lama_api_key = st.secrets["lamapoll_api_key"]
poll_id = 1965090

df = common.fetch_participants_df(lama_api_key, poll_id)
common.render_participant_figures(df)

df_devices = common.fetch_devices_df(lama_api_key, poll_id)
common.render_devices_figure(df_devices)

common.section_gap()

question_categories = [
    (29603193, "Gender"),
    (29603199, "Hyposmia"),
    (29603202, "RBDSQ"),
    (29603205, "Memory Loss"),
    (29603208, "Family History of PD"),
    (29603211, "Family member with PD"),
    (29603496, "ND (Clinical)"),
]

question_tabs = st.tabs([name for _, name in question_categories])
for i, (tab, (question_id, name)) in enumerate(zip(question_tabs, question_categories)):
    with tab:
        common.lamapoll_question_results_barchart(lama_api_key, poll_id, question_id, name, fig_number=4 + i)
