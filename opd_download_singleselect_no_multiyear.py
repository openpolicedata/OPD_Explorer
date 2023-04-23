import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import copy
import openpolicedata as opd


#
if 't_data' not in st.session_state:
    st.session_state['t_data'] = None

t_data = st.session_state['t_data']

if 'collect_data_state' not in st.session_state:
    st.session_state['collect_data_state'] = "NOT_STARTED"


# @st.cache
@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    df = df[~df['Year'].isin(['MULTI', 'NONE'])]
    df['Year'] = df['Year'].astype(str)
    return df

# @st.cache(allow_output_mutation=True)


@st.cache_data
def get_traffic_data(source_name, year, table_type, agency):
    src = opd.Source(source_name=source_name)

    t_data = src.load_from_url(year=year, table_type=table_type, agency=agency)
    return t_data


data_catalog = get_data_catalog()

st.header('Selected dataset to download')
expander_container = st.container()

# Define the data as a dictionary
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Age': [25, 30, 35, 40],
    'City': ['New York', 'San Francisco', 'Los Angeles', 'Chicago']
}

# Create a pandas DataFrame from the dictionary
collect_help = "This collects the data from the data source such as a URL and will make it ready for download. This may take some time."
# , on_click=None
if st.session_state['collect_data_state'] in ["NOT_STARTED"] and st.button('Collect data from source to make ready download', help=collect_help):
    st.session_state['collect_data_state'] = "COLLECTING_DATA"

if st.session_state['collect_data_state'] in ["COLLECTING_DATA"]:
    selected_rows = pd.DataFrame(data)
    csv_text = selected_rows.to_csv(index=False)
    st.session_state['csv_text'] = csv_text
    st.session_state['collect_data_state']="READY_TO_DOWNLOAD_DATA"
    
if st.session_state['collect_data_state'] in ["READY_TO_DOWNLOAD_DATA"] and st.download_button('Download CSV', data=st.session_state['csv_text'] , file_name="selected_rows.csv", mime='text/csv'):
    st.session_state['collect_data_state']="NOT_STARTED"

show_all_datasets = st.checkbox('Show all datasets available')
if show_all_datasets == True:
    st.dataframe(data=data_catalog)

with st.sidebar:
    selectbox_states = st.selectbox('States', pd.unique(
        data_catalog['State']), help='Select the states you want to download data for')
    if len(selectbox_states) == 0:
        # make a copy of data_catalog
        selected_rows = copy.deepcopy(data_catalog)
    else:
        selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]

    selectbox_sources = st.selectbox('Available sources', pd.unique(
        pd.unique(selected_rows['SourceName'])), help='Select the sources')

    if len(selectbox_sources) == 0:
        # make a copy of data_catalog pandas dataframe
        selected_rows = copy.deepcopy(selected_rows)
    else:
        # todo filter selected_rows by State and SourceName
        selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]

    selectbox_table_types = st.selectbox('Available table types', pd.unique(
        pd.unique(selected_rows['TableType'])), help='Select the table type')

    if len(selectbox_table_types) == 0:
        # make a copy of data_catalog pandas dataframe
        selected_rows = copy.deepcopy(selected_rows)
    else:
        # todo filter selected_rows by State and SourceName
        selected_rows = selected_rows[selected_rows['TableType'].isin(
            [selectbox_table_types])]

    selectbox_years = st.selectbox('Available years', pd.unique(
        pd.unique(selected_rows['Year'])), help='Select the year')

    if len(selectbox_years) == 0:
        # make a copy of data_catalog pandas dataframe
        selected_rows = copy.deepcopy(selected_rows)
    else:
        # todo filter selected_rows by State and SourceName
        selected_rows = selected_rows[selected_rows['Year'].isin([selectbox_years])]


with expander_container:
    st.dataframe(data=selected_rows)