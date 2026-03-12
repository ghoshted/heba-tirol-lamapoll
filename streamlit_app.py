import streamlit as st
import requests
import json
import pandas as pd
import datetime
import altair as alt

st.logo("https://github.com/ghoshted/biocore_cti_artefacts/blob/main/UNI_Logo_Inter_LCSB_rgb2.png?raw=true", size="large")
today = datetime.date.today()
st.sidebar.markdown("**HeBA/Tirol/OSQ/Report**")
st.markdown("### HeBA/Tirol/OSQ/Report")
st.badge(str(today))

lama_api_key= st.secrets["lamapoll_api_key"]

url = 'https://app.lamapoll.de/api/v2/polls/1965090/statistics'
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
    st.write(f"Error making API request: {e}")
except json.JSONDecodeError:
    st.write(f"Error decoding JSON response. Response content: {response.text}")

url_mailing = 'https://app.lamapoll.de/api/v2/polls/1965090/mailings'

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
    st.write(f"Error making API request for mailings: {e}")
except json.JSONDecodeError:
    st.write(f"Error decoding JSON response for mailings. Response content: {response_mailing.text}")
df_mailing = pd.DataFrame(data_mailing)

#df_mailing = df_mailing[df_mailing['attributes'].str.contains('Tirol|TIROL', case=False, na=False)]
# Convert attributes to string first, then filter
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

col0, col1, col2, col3 = st.columns(4)
col0.metric("Total invited", df_mailing_invited)
col1.metric("Total Visitors", visitors_total, delta=str(round((visitors_total/df_mailing_invited)*100, 2))+"% of invited", delta_arrow="off")
col2.metric("Total Started", started_total, delta=str(round((started_total/visitors_total)*100, 2))+"% of visitors", delta_arrow="off")
col3.metric("Total Finished", finished_total, delta=str(round((finished_total/started_total)*100, 2))+"% of started", delta_arrow="off")

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
    print(f"Error making API request: {e}")
except json.JSONDecodeError:
    print(f"Error decoding JSON response. Response content: {response.text}")

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