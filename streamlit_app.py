import streamlit as st
import requests
import json
import pandas as pd
import datetime
import altair as alt

with st.sidebar:
    st.image("https://res.cloudinary.com/dpr5x9upe/image/upload/v1773355468/lcsb_cti_logo_yoefzu.png")

    st.markdown("**Healthy Brain Ageing (HeBA) Study | Reports**")
    st.caption("This dashboard provides insights into the HeBA/Tirol/OSQ survey data, including participant engagement and device usage statistics. The data is sourced from the LamaPoll API and is updated regularly to reflect the latest trends and patterns in participant behavior.")
    st.caption("[LCSB](https://www.uni.lu/lcsb) | soumyabrata.ghosh@uni.lu")
st.markdown("### HeBA/Tirol/OSQ/Report")

today = datetime.date.today()
st.badge(str(today))

lama_api_key= st.secrets["lamapoll_api_key"]
poll_id = 1965090
def get_lama_response_data(lama_api_key,poll_id):
    url = f'https://app.lamapoll.de/api/v2/polls/{poll_id}/statistics'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+str(lama_api_key)
    }
    params = {
        'interval': 'day',
        'include[]': 'participants'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        #print(json.dumps(data, indent=2))
        #st.success('API request successful. Data retrieved and parsed as JSON.')
    except requests.exceptions.RequestException as e:
        st.warning(f"Error making API request: {e}")
    except json.JSONDecodeError:
        st.warning(f"Error decoding JSON response. Response content: {response.text}")
    return data

data = get_lama_response_data(lama_api_key,poll_id)


def get_lama_response_data_mailing(lama_api_key,poll_id):
    url_mailing = f'https://app.lamapoll.de/api/v2/polls/{poll_id}/mailings'

    headers_mailing = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+str(lama_api_key)
    }
    params_mailing = {
        'offset': 6,
        'status': 'done'
    }
    try:
        response_mailing = requests.get(url_mailing, headers=headers_mailing, params=params_mailing)
        response_mailing.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data_mailing = response_mailing.json()
        #print(json.dumps(data_mailing, indent=2))
        #st.success('API request for mailings successful. Data retrieved and parsed as JSON.')
    except requests.exceptions.RequestException as e:
        st.warning(f"Error making API request for mailings: {e}")
    except json.JSONDecodeError:
        st.warning(f"Error decoding JSON response for mailings. Response content: {response_mailing.text}")
    return data_mailing


def get_question_results(lama_api_key,poll_id,question_id):
    url = f'https://app.lamapoll.de/api/v2/polls/{poll_id}/questions/{question_id}/results'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + str(lama_api_key)
    }
    params = {
        'lang': 'de'
    }
    data = {}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"Error making API request: {e}")
    except json.JSONDecodeError:
        st.warning(f"Error decoding JSON response. Response content: {response.text}")
    return data

def to_dataframe_safe(value):
    """Convert API response data to a pandas DataFrame safely.

    LamaPoll can return nested dicts, dicts with a single list value, or lists.
    This helper tries common conversions and falls back to json_normalize.
    """

    try:
        return pd.DataFrame(value)
    except Exception:
        # If response is a dict with one list value, use that list
        if isinstance(value, dict) and len(value) == 1:
            first_val = next(iter(value.values()))
            if isinstance(first_val, list):
                return pd.DataFrame(first_val)
        return pd.json_normalize(value)

# 1965090, 29603193

def lamapoll_question_results_barchart(lama_api_key, poll_id, question_id, category_name):
    result_sex = get_question_results(lama_api_key, poll_id, question_id)
    result_sex_df = to_dataframe_safe(result_sex)

    # Extract labels and frequencies
    labels = result_sex_df['groups'][0][0]['labels']
    items = result_sex_df['groups'][0][0]['items']

    # Combine labels with their frequency data
    sex_data = []
    for i, label in enumerate(labels):
        # Check if the item exists before accessing it
        # st.write(f"Processing {i} label: {label}")
        abs_value = items[0]['freq']['abs'][i]
        sex_data.append({'Category': label, 'Count': abs_value})

    # Create DataFrame for visualization
    df_sex = pd.DataFrame(sex_data)

    # Create bar chart
    sex_chart = alt.Chart(df_sex).mark_bar().encode(
        x=alt.X('Category:N', title=str(category_name)),
        y=alt.Y('Count:Q', title='Number of Responses'),
        color='Category:N'
    ).properties(
       # width=600,
       # height=400,
        title=f"Survey Responses by {category_name}"
    )
    st.altair_chart(sex_chart, theme="streamlit", use_container_width=True)

    # Also display the data in a table
    st.dataframe(df_sex, use_container_width=True)


#if st.button("Refresh Data", type="primary"):
#    data = get_lama_response_data(lama_api_key, poll_id)
#    data_mailing = get_lama_response_data_mailing(lama_api_key, poll_id)
#    result_sex = get_question_results(lama_api_key, poll_id, question_id)
try:
    data_mailing = get_lama_response_data_mailing(lama_api_key,poll_id)
except Exception as e:
    st.warning(f"Error occurred while fetching mailing data: {e}")
    data_mailing = []  # Set to empty list if fetching fails
try:
    df_mailing = pd.DataFrame(data_mailing)
except Exception as e:
    df_mailing = pd.DataFrame()  # Create an empty DataFrame if conversion fails
    st.warning(f"Error occurred while creating DataFrame for mailing data: {e}")

#df_mailing = df_mailing[df_mailing['attributes'].str.contains('Tirol|TIROL', case=False, na=False)]
# Convert attributes to string first, then filter
if 'attributes' in df_mailing.columns:
    df_mailing['attributes_str'] = df_mailing['attributes'].astype(str)
    df_mailing = df_mailing[df_mailing['attributes_str'].str.contains('Tirol|TIROL', case=False, na=False)]
    df_mailing = df_mailing.drop('attributes_str', axis=1)  # Remove the temporary column if not needed
    df_mailing_invited = df_mailing['numOfReceivers'].sum()

dates = []
started_participants = []
finished_participants = []
visitors = []

for entry in data:
    dates.append(pd.to_datetime(entry['startDate']))
    participants_data = entry['participants']
    started_participants.append(participants_data['started'])
    finished_participants.append(participants_data['finished'])
    visitors.append(participants_data['visitors'])

#st.success("Data extraction complete. Lists are ready for DataFrame creation.")

df = pd.DataFrame({
    'Date': dates,
    'Started': started_participants,
    'Finished': finished_participants,
    'Visitors': visitors
})
df = df.set_index('Date')
visitors_total = df['Visitors'].sum()
started_total = df['Started'].sum()
finished_total = df['Finished'].sum()
if 'df_mailing_invited' in locals():
    col0, col1, col2, col3 = st.columns(4)
    col0.metric("Total invited", df_mailing_invited)
    col1.metric("Total Visitors", visitors_total, delta=str(round((visitors_total/df_mailing_invited)*100, 2))+"% of invited", delta_arrow="off")
    col2.metric("Total Started", started_total, delta=str(round((started_total/visitors_total)*100, 2))+"% of visitors", delta_arrow="off")
    col3.metric("Total Finished", finished_total, delta=str(round((finished_total/started_total)*100, 2))+"% of started", delta_arrow="off")
else:
    col0, col1, col2 = st.columns(3)
    col0.metric("Total Visitors", visitors_total)
    col1.metric("Total Started", started_total, delta=str(round((started_total/visitors_total)*100, 2))+"% of visitors", delta_arrow="off")
    col2.metric("Total Finished", finished_total, delta=str(round((finished_total/started_total)*100, 2))+"% of started", delta_arrow="off")

#st.success("DataFrame created successfully with 'Date' as index.")
#df.head()
st.line_chart(df, color=['#7AAACE', '#355872', '#9CD5FF'])

## Devices data
url = 'https://app.lamapoll.de/api/v2/polls/1965090/statistics'
headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer '+str(lama_api_key)
}
params = {
    'include[]': 'userDevices'
}

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    data_devices = response.json()
    #print(json.dumps(data, indent=2))
except requests.exceptions.RequestException as e:
    st.warning(f"Error making API request: {e}")
except json.JSONDecodeError:
    st.warning(f"Error decoding JSON response. Response content: {response.text}")

# Extract the userDevices data, which is a list of dictionaries
devices_data = data_devices[0]['userDevices']

# Create a DataFrame
df_devices = pd.DataFrame(devices_data)

print("DataFrame 'df_devices' created successfully.")
#st.dataframe(df_devices)



col1, col2, col3 = st.columns(3)

with col1:
    browser = alt.Chart(df_devices).mark_bar().encode(
        x='browser',
        y='sum(cnt)'
    )
    st.altair_chart(browser, theme="streamlit", use_container_width=True)
with col2:
    devices = alt.Chart(df_devices).mark_bar().encode(
        x='deviceType',
        y='sum(cnt)'
    )
    st.altair_chart(devices, theme="streamlit", use_container_width=True)
with col3:
    os = alt.Chart(df_devices).mark_bar().encode(
        x='os',
        y='sum(cnt)'
    )
    st.altair_chart(os, theme="streamlit", use_container_width=True)



# from streamlit_echarts import st_echarts
#
# options = {
#     "xAxis": {
#         "type": "category",
#         "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
#     },
#     "yAxis": {"type": "value"},
#     "series": [{"data": [820, 932, 901, 934, 1290, 1330, 1320], "type": "bar"}],
# }
#
# st_echarts(options=options, height="400px")

col4, col5, col6, col7, col8, col9 = st.tabs(["Gender", "Hyposmia", "RBDSQ", "Memory Loss", "Family History of PD", "Family member with PD"])

with col4:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603193,"Gender")
with col5:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603199,"Hyposmia")
with col6:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603202,"RBDSQ")
with col7:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603205,"Memory Loss")
with col8:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603208,"Family History of PD")
with col9:
    lamapoll_question_results_barchart(lama_api_key, poll_id, 29603211,"Family member with PD")