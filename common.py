import hmac
import html
from pathlib import Path

import streamlit as st
import requests
import json
import pandas as pd
import altair as alt

ASSETS = Path(__file__).parent / "assets"

ACCENT = "#2E4257"
ACCENT_LIGHT = "#8CA3B5"
ACCENT_PALE = "#CBD4DA"
ACCENT_SIENNA = "#8A5A3B"
ACCENT_SIENNA_LIGHT = "#C9AC91"
ACCENT_MOSS = "#3F5B4C"
INK = "#15140F"
SOFT = "#57534A"
MUTED = "#6B675E"
RULE_MID = "rgba(21, 20, 15, 0.55)"
HAIR = "rgba(21, 20, 15, 0.14)"
TICK = "rgba(21, 20, 15, 0.35)"
MONO_FONT = "IBM Plex Mono"

PAGES = [
    st.Page("pages/tirol.py", title="Tirol", default=True),
    st.Page("pages/luxembourg.py", title="Luxembourg"),
]


def inject_css():
    css = (ASSETS / "tokens.css").read_text() + "\n" + (ASSETS / "adept.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def eyebrow(text):
    st.markdown(f'<div class="tp-eyebrow">{text}</div>', unsafe_allow_html=True)


def display_heading(text):
    st.markdown(f'<h1 class="tp-display">{text}</h1>', unsafe_allow_html=True)


def qualifier(text):
    st.markdown(f'<div class="tp-qualifier">{text}</div>', unsafe_allow_html=True)


def header_rule():
    st.markdown('<hr class="tp-header-rule" />', unsafe_allow_html=True)


def panel_head(kind, number, title, qualifier_text, tight=False):
    css_class = "tp-panel-head tp-panel-head--tight" if tight else "tp-panel-head"
    st.markdown(
        f'<div class="{css_class}">'
        f'<div class="tp-panel-head__title">{kind} {number} — {html.escape(title)}</div>'
        f'<div class="tp-panel-head__qualifier">{html.escape(qualifier_text)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def subpanel_label(text):
    st.markdown(f'<div class="tp-subpanel-label">{text}</div>', unsafe_allow_html=True)


def section_gap():
    st.markdown('<div class="tp-section-gap"></div>', unsafe_allow_html=True)


def stat_cells(cells):
    rows = "".join(
        '<div class="tp-stat-cell">'
        f'<div class="tp-stat-cell__label">{html.escape(c["label"])}</div>'
        f'<div class="tp-stat-cell__value">{html.escape(c["value"])}</div>'
        f'<div class="tp-stat-cell__note">{html.escape(c["note"])}</div>'
        "</div>"
        for c in cells
    )
    st.markdown(f'<div class="tp-stat-row">{rows}</div>', unsafe_allow_html=True)


def mono_legend(items):
    swatches = "".join(
        '<span class="tp-legend__item">'
        f'<span class="tp-legend__swatch" style="background:{color}"></span>{html.escape(label)}'
        "</span>"
        for label, color in items
    )
    st.markdown(f'<div class="tp-legend">{swatches}</div>', unsafe_allow_html=True)


def alert(label, message):
    st.markdown(
        f'<div class="tp-alert"><div class="tp-alert__label">{label}</div>'
        f'<div class="tp-alert__body">{message}</div></div>',
        unsafe_allow_html=True,
    )


def adept_chart(chart):
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(
            domainColor=RULE_MID,
            gridColor=HAIR,
            tickColor=TICK,
            tickSize=3,
            labelFont=MONO_FONT,
            labelFontSize=11,
            labelColor=MUTED,
            labelFontWeight="normal",
            titleFont=MONO_FONT,
            titleFontSize=11,
            titleColor=SOFT,
            titleFontWeight="normal",
        )
        .configure_legend(disable=True)
    )


def require_password(secret_key, nav_title):
    """Gate the calling page behind a password scoped to secret_key.

    Returns immediately if the current session already authenticated for this
    page; otherwise renders a sign-in form (with the sidebar nav still active,
    so other pages remain reachable) and halts with st.stop(), so no data
    fetch or page content runs before authentication succeeds.
    """
    session_flag = f"authed_{secret_key}"
    if st.session_state.get(session_flag):
        return

    inject_css()
    render_sidebar(active_title=nav_title)

    eyebrow("LCSB · Reports")
    display_heading(f"Site:{nav_title} - Sign in")
    qualifier(f"Site:{nav_title} requires a password.")
    header_rule()

    with st.form(f"password_form_{secret_key}"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted:
        expected = st.secrets.get("passwords", {}).get(secret_key)
        if expected and hmac.compare_digest(entered, expected):
            st.session_state[session_flag] = True
            st.rerun()
        else:
            alert("Note", "Incorrect password.")

    st.stop()


def render_sidebar(active_title=None, auth_key=None):
    with st.sidebar:
        eyebrow("LCSB · Reports")
        st.markdown(
            '<p style="font-size:18px;color:var(--tp-ink);margin:2px 0 12px 0;">'
            "Healthy Brain Ageing (HeBA) Study</p>",
            unsafe_allow_html=True,
        )
        for page in PAGES:
            if page.title == active_title:
                st.markdown('<div class="tp-nav-active-marker"></div>', unsafe_allow_html=True)
            st.page_link(page)
        st.caption(
            "This report summarises HeBA survey sites: participant engagement, "
            "device usage, and response distributions."
        )
        st.caption("[LCSB](https://www.uni.lu/lcsb) · soumyabrata.ghosh@uni.lu")
        if auth_key:
            if st.button("Log out", key=f"logout_{auth_key}"):
                st.session_state.pop(f"authed_{auth_key}", None)
                st.rerun()
        st.image("https://res.cloudinary.com/dpr5x9upe/image/upload/v1773355468/lcsb_cti_logo_yoefzu.png")


def get_lama_response_data(lama_api_key, poll_id):
    url = f"https://app.lamapoll.de/api/v2/polls/{poll_id}/statistics"
    headers = {"accept": "application/json", "Authorization": "Bearer " + str(lama_api_key)}
    params = {"interval": "day", "include[]": "participants"}
    data = []
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        alert("Note", f"Request to the LamaPoll API failed: {html.escape(str(e))}")
    except json.JSONDecodeError:
        alert("Note", f"The API response could not be decoded as JSON: {html.escape(response.text)}")
    return data


def get_question_results(lama_api_key, poll_id, question_id):
    url = f"https://app.lamapoll.de/api/v2/polls/{poll_id}/questions/{question_id}/results"
    headers = {"accept": "application/json", "Authorization": "Bearer " + str(lama_api_key)}
    params = {"lang": "de"}
    data = {}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        alert("Note", f"Request to the LamaPoll API failed: {html.escape(str(e))}")
    except json.JSONDecodeError:
        alert("Note", f"The API response could not be decoded as JSON: {html.escape(response.text)}")
    return data


def to_dataframe_safe(value):
    """Convert API response data to a pandas DataFrame safely.

    LamaPoll can return nested dicts, dicts with a single list value, or lists.
    This helper tries common conversions and falls back to json_normalize.
    """
    try:
        return pd.DataFrame(value)
    except Exception:
        if isinstance(value, dict) and len(value) == 1:
            first_val = next(iter(value.values()))
            if isinstance(first_val, list):
                return pd.DataFrame(first_val)
        return pd.json_normalize(value)


def fetch_participants_df(lama_api_key, poll_id):
    data = get_lama_response_data(lama_api_key, poll_id)
    dates, started_participants, finished_participants, visitors = [], [], [], []
    for entry in data:
        dates.append(pd.to_datetime(entry["startDate"]))
        participants_data = entry["participants"]
        started_participants.append(participants_data["started"])
        finished_participants.append(participants_data["finished"])
        visitors.append(participants_data["visitors"])
    return pd.DataFrame(
        {"Date": dates, "Started": started_participants, "Finished": finished_participants, "Visitors": visitors}
    ).set_index("Date")


def fetch_devices_df(lama_api_key, poll_id):
    url = f"https://app.lamapoll.de/api/v2/polls/{poll_id}/statistics"
    headers = {"accept": "application/json", "Authorization": "Bearer " + str(lama_api_key)}
    params = {"include[]": "userDevices"}
    data_devices = []
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data_devices = response.json()
    except requests.exceptions.RequestException as e:
        alert("Note", f"Request to the LamaPoll API failed: {html.escape(str(e))}")
    except json.JSONDecodeError:
        alert("Note", f"The API response could not be decoded as JSON: {html.escape(response.text)}")
    devices_data = data_devices[0]["userDevices"] if data_devices else []
    return pd.DataFrame(devices_data)


def device_bar(df_devices, dim):
    grouped = df_devices.groupby(dim, as_index=False)["cnt"].sum()
    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{dim}:N",
                title=None,
                sort="-y",
                axis=alt.Axis(labelAngle=-90, labelLimit=200, labelOverlap=False, labelAlign="right", labelBaseline="middle"),
            ),
            y=alt.Y("cnt:Q", title=None),
            color=alt.Color("cnt:Q", scale=alt.Scale(range=[ACCENT_PALE, ACCENT]), legend=None),
            tooltip=[dim, "cnt"],
        )
        .properties(height=300)
    )
    st.altair_chart(adept_chart(chart), use_container_width=True)


def render_participant_figures(df):
    visitors_total = int(df["Visitors"].sum())
    started_total = int(df["Started"].sum())
    finished_total = int(df["Finished"].sum())
    started_pct = (started_total / visitors_total * 100) if visitors_total else 0
    finished_of_started_pct = (finished_total / started_total * 100) if started_total else 0

    stat_cells(
        [
            {"label": "Total visitors", "value": f"{visitors_total:,}", "note": "recorded sessions"},
            {"label": "Total started", "value": f"{started_total:,}", "note": f"{started_pct:.1f}% of visitors"},
            {"label": "Total completed", "value": f"{finished_total:,}", "note": f"{finished_of_started_pct:.1f}% of started"},
        ]
    )
    section_gap()

    series_colors = {"Started": ACCENT_LIGHT, "Completed": ACCENT_MOSS, "Visitors": ACCENT_SIENNA_LIGHT}
    df_participants_melted = (
        df.rename(columns={"Finished": "Completed"}).reset_index().melt("Date", var_name="Metric", value_name="Value")
    )
    participants_chart = (
        alt.Chart(df_participants_melted)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title=None),
            color=alt.Color(
                "Metric:N",
                scale=alt.Scale(domain=list(series_colors.keys()), range=list(series_colors.values())),
                legend=None,
            ),
            tooltip=["Date:T", "Metric:N", "Value:Q"],
        )
        .properties(height=320)
    )

    df_cumulative_finished = df.sort_index().reset_index()
    df_cumulative_finished["Cumulative Completed"] = df_cumulative_finished["Finished"].cumsum()
    cumulative_finished_chart = (
        alt.Chart(df_cumulative_finished)
        .mark_line(strokeWidth=2, color=ACCENT)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Cumulative Completed:Q", title=None),
            tooltip=["Date:T", "Cumulative Completed:Q"],
        )
        .properties(height=320)
    )

    n_days = len(df)
    tab_series, tab_cumulative = st.tabs(["Series", "Cumulative"])
    with tab_series:
        panel_head("Fig.", 1, "Participants over time", f"n = {visitors_total:,} · {n_days} days", tight=True)
        st.altair_chart(adept_chart(participants_chart), use_container_width=True)
        mono_legend(list(series_colors.items()))
    with tab_cumulative:
        panel_head("Fig.", 2, "Cumulative completed participants", f"Σ = {finished_total:,}", tight=True)
        st.altair_chart(adept_chart(cumulative_finished_chart), use_container_width=True)


def render_devices_figure(df_devices):
    devices_total = int(df_devices["cnt"].sum()) if not df_devices.empty else 0
    panel_head("Fig.", 3, "Device, browser, and operating system distribution", f"n = {devices_total:,}")

    if df_devices.empty:
        alert("Note", "No device data is available for this poll.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        subpanel_label("Browser")
        device_bar(df_devices, "browser")
    with col2:
        subpanel_label("Device")
        device_bar(df_devices, "deviceType")
    with col3:
        subpanel_label("OS")
        device_bar(df_devices, "os")


def lamapoll_question_results_barchart(lama_api_key, poll_id, question_id, category_name, fig_number):
    result = get_question_results(lama_api_key, poll_id, question_id)
    result_df = to_dataframe_safe(result)

    if result_df.empty or "groups" not in result_df.columns:
        panel_head("Fig.", fig_number, category_name, "n = 0", tight=True)
        alert("Note", f"No results are available for {html.escape(category_name)}.")
        return

    labels = result_df["groups"][0][0]["labels"]
    items = result_df["groups"][0][0]["items"]
    rows = [{"Category": label, "Count": items[0]["freq"]["abs"][i]} for i, label in enumerate(labels)]
    df_cat = pd.DataFrame(rows)
    total = int(df_cat["Count"].sum()) if not df_cat.empty else 0

    panel_head("Fig.", fig_number, category_name, f"n = {total:,}", tight=True)

    if total == 0:
        alert("Note", f"No responses are recorded for {html.escape(category_name)}.")
        return

    chart = (
        alt.Chart(df_cat)
        .mark_bar()
        .encode(
            x=alt.X(
                "Category:N",
                title=None,
                sort="-y",
                axis=alt.Axis(labelAngle=-90, labelLimit=250, labelOverlap=False, labelAlign="right", labelBaseline="middle"),
            ),
            y=alt.Y("Count:Q", title=None),
            color=alt.Color("Count:Q", scale=alt.Scale(range=[ACCENT_PALE, ACCENT]), legend=None),
            tooltip=[alt.Tooltip("Category:N", title=category_name), alt.Tooltip("Count:Q", title="Responses")],
        )
        .properties(height=340)
    )

    st.altair_chart(adept_chart(chart), use_container_width=True)

    panel_head("Tab.", fig_number - 3, category_name, f"n = {total:,}")
    st.dataframe(df_cat, use_container_width=True, hide_index=True)
