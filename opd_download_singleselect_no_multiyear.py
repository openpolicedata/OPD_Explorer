import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import copy
import openpolicedata as opd

import io
import random
import string

class RandomASCIIReader(io.BufferedReader):
    def __init__(self, length: int, seed: int = None):
        # Seed the random generator, if specified
        if seed is not None:
            random.seed(seed)

        self.length = length
        self.seed = seed

    def read(self, size: int = -1) -> bytes:
        # If size is negative or greater than the specified length, set it to the length
        if size < 0 or size > self.length:
            size = self.length

        # Generate random ASCII characters of the specified size
        random_chars = ''.join(random.choice(string.ascii_letters) for _ in range(size))

        # Encode the string as bytes
        random_data = random_chars.encode('ascii')

        # Return the random data
        return random_data
    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        # Do nothing, since seeking is not supported for this reader
        pass
    
class URLDataReader(io.BufferedReader):
    def __init__(self, selected_rows, length: int, seed: int = None):
        # Seed the random generator, if specified
        if seed is not None:
            random.seed(seed)

        self.length = length
        self.seed = seed
        self.selected_rows = selected_rows

    def read(self, size: int = -1) -> bytes:
        # If size is negative or greater than the specified length, set it to the length
        if size < 0 or size > self.length:
            size = self.length
        
        selected_rows = self.selected_rows
        if selected_rows is None:
            return b''
        
        print(f'***source_name={selected_rows.iloc[0]["SourceName"]}, state={selected_rows.iloc[0]["State"]}')
        src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])        
        types = src.get_tables_types()
        print(types)
        years = src.get_years(table_type=types[0])
        print(years)
        print(f'***year={selected_rows.iloc[0]["Year"]}, table_type={selected_rows.iloc[0]["TableType"]}')
        data_from_url = src.load_from_url(year=int(selected_rows.iloc[0]["Year"]), table_type=selected_rows.iloc[0]["TableType"]) 
        #data_from_url = src.load_from_url(year=2021, table_type='TRAFFIC STOPS')     
        csv_text = data_from_url.table.to_csv(index=False)
        return csv_text.encode('utf-8', 'surrogateescape')

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        # Do nothing, since seeking is not supported for this reader
        pass


def get_data_from_url(selected_rows):
    src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])
    data_from_url = src.load_from_url(year=int(selected_rows.iloc[0]["Year"]), table_type=selected_rows.iloc[0]["TableType"]) 
    csv_text = data_from_url.table.to_csv(index=False)
    return csv_text.encode('utf-8', 'surrogateescape')
    
if 't_data' not in st.session_state:
    st.session_state['t_data'] = None

t_data = st.session_state['t_data']

if 'collect_data_state' not in st.session_state:
    st.session_state['collect_data_state'] = "NOT_STARTED"

if 'selected_rows' not in st.session_state:    
    st.session_state['selected_rows'] = None

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
# if st.session_state['collect_data_state'] in ["NOT_STARTED"] and st.button('Collect data from source to make ready download', help=collect_help):
#     st.session_state['collect_data_state'] = "COLLECTING_DATA"
    

# if st.session_state['collect_data_state'] in ["COLLECTING_DATA"]:
    
#     selected_rows = st.session_state['selected_rows']
#     print(f'***source_name={selected_rows.iloc[0]["SourceName"]}, state={selected_rows.iloc[0]["State"]}')
#     # #src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])
#     # src = opd.Source(source_name="Montgomery County", state="Maryland")
#     # # Load traffic stop data for 2021
#     # types = src.get_tables_types()
#     # print(types)
#     # years = src.get_years(table_type=types[0])
#     # print(years)
#     # print(f'***year={selected_rows.iloc[0]["Year"]}, table_type={selected_rows.iloc[0]["TableType"]}')
#     # #data_from_url = src.load_from_url(year=int(selected_rows.iloc[0]["Year"]), table_type=selected_rows.iloc[0]["TableType"]) 
#     # #data_from_url = src.load_from_url(year=2021, table_type='TRAFFIC STOPS')     
#     # # csv_text = data_from_url.table.to_csv(index=False)
    

#     csv_text="hi!"
#     st.session_state['csv_text'] = csv_text.encode('utf-8', 'surrogateescape')
#     st.session_state['collect_data_state']="READY_TO_DOWNLOAD_DATA"
    
length = 100
seed = 42  # Optional, to get reproducible random data

    
# if st.session_state['collect_data_state'] in ["READY_TO_DOWNLOAD_DATA"] and st.download_button('Download CSV', data=URLDataReader(st.session_state['selected_rows'], length, seed) , file_name="selected_rows.csv", mime='text/csv'):
#     st.session_state['collect_data_state']="NOT_STARTED"
if st.download_button('Download CSV', data=URLDataReader(st.session_state['selected_rows'], length, seed) , file_name="selected_rows.csv", mime='text/csv'):
    print('Download complete')



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
    st.session_state['selected_rows']=selected_rows

with expander_container:
    st.dataframe(data=selected_rows)