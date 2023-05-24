import streamlit as st
import pandas as pd
import logging

import openpolicedata as opd


# https://discuss.streamlit.io/t/streamlit-duplicates-log-messages-when-stream-handler-is-added/16426/4
def create_logger(name, level='INFO', file=None, addtime=False):
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    if addtime:
        format = "%(asctime)s :: %(message)s"
    else:
        format = '%(message)s'
    #if no streamhandler present, add one
    if sum([isinstance(handler, logging.StreamHandler) for handler in logger.handlers]) == 0:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(format, '%y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)
    #if a file handler is requested, check for existence then add
    if file is not None:
        if sum([isinstance(handler, logging.FileHandler) for handler in logger.handlers]) == 0:
            ch = logging.FileHandler(file, 'w')
            ch.setFormatter(logging.Formatter(format, '%y-%m-%d %H:%M:%S'))
            logger.addHandler(ch)
        
    return logger

if 'logger' not in st.session_state:
    st.session_state['logger'] = create_logger(name = 'opd-app', level = 'DEBUG')
logger = st.session_state['logger']

#create a global flag to say if should download or not  (default to false)  

if 'show_download' not in st.session_state:    
    logger.debug("Reset download flag")
    st.session_state['show_download'] = False
else:
    logger.debug("SKIP reset download flag")

if 'data_from_url' not in st.session_state:    
    st.session_state['data_from_url'] = None

if 'selected_rows' not in st.session_state:  
    st.session_state['selected_rows'] = None
    logger.debug(f"'selected_rows' NOT IN in st.session_state. st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
else:
    selected_rows=st.session_state['selected_rows']
    logger.debug(f"'selected_rows' IN st.session_state. st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
    
@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    df['Year'] = df['Year'].astype(str)
    return df


data_catalog = get_data_catalog()
st.title('Open Police Data')


st.header('Filtered dataset')
expander_container = st.container()


with st.sidebar:
    st.header('Dataset Filters')
    selectbox_states = st.selectbox('States', data_catalog['State'].unique(), 
                                    help='Select the states you want to download data for')
    logger.debug(f"selectbox_states = {selectbox_states}")
    if len(selectbox_states) == 0:
        selected_rows = data_catalog.copy()
        logger.debug(f"selectbox_states == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]
        logger.debug(f"selectbox_states != 0, selected_rows = {selected_rows}")

    selectbox_sources = st.selectbox('Available sources', selected_rows['SourceName'].unique(), 
                                     help='Select the sources')

    if len(selectbox_sources) == 0:
        logger.debug(f"selectbox_sources == 0, selected_rows = {selected_rows}")
    else:        
        selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]
        logger.debug(f"selectbox_sources != 0, selected_rows = {selected_rows}")

    selectbox_table_types = st.selectbox('Available table types', selected_rows['TableType'].unique(), 
                                         help='Select the table type')

    if len(selectbox_table_types) == 0:       
        logger.debug(f"selectbox_table_types == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = selected_rows[selected_rows['TableType'].isin(
            [selectbox_table_types])]
        logger.debug(f"selectbox_table_types != 0, selected_rows = {selected_rows}")

    selectbox_years = st.selectbox('Available years', pd.unique(
       selected_rows['Year']), help='Select the year')

    if len(selectbox_years) == 0:
        print(f"selectbox_years == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = selected_rows[selected_rows['Year'].isin([selectbox_years])]
        print(f"selectbox_years != 0, selected_rows = {selected_rows}")
        
    st.session_state['selected_rows']=selected_rows
logger.debug(f"selected_rows = {selected_rows}")



collect_help = "This collects the data from the data source such as a URL and will make it ready for download. This may take some time."

if st.session_state['show_download'] == True:
    if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name="selected_rows.csv", mime='text/csv'):
        st.session_state['show_download'] = False
        logger.debug('Download complete!!!!!')
        st.session_state['csv_text_output'] = None
        st.experimental_rerun()
 
else:
    if st.button('Collect data', help=collect_help):
        logger.debug(f'***source_name={selected_rows.iloc[0]["SourceName"]}, state={selected_rows.iloc[0]["State"]}')
        src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])        
        types = src.get_tables_types()
        logger.debug(f"types = {types}")
        years = src.get_years(table_type=types[0])
        logger.debug(f"years = {years}")
        logger.debug(f'***year={selected_rows.iloc[0]["Year"]}, table_type={selected_rows.iloc[0]["TableType"]}')
        logger.debug("Downloading data from URL")
        data_from_url = src.load_from_url(year=int(selected_rows.iloc[0]["Year"]), table_type=selected_rows.iloc[0]["TableType"]) 
        logger.debug(f"Data downloaded from URL. Total of {len(data_from_url.table)} rows")
        csv_text = data_from_url.table.to_csv(index=False)
        csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
        st.session_state['data_from_url'] = data_from_url
        st.session_state['csv_text_output'] = csv_text_output
        #st.dataframe(data=selected_rows)
        st.session_state['show_download'] = True
        logger.debug(f"csv_text_output len is {len(csv_text_output)}  type(csv_text_output) = {type(csv_text_output)}")
        logger.debug(f"st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
        st.session_state['selected_rows']=selected_rows
        st.experimental_rerun()
        
# if (st.session_state['data_from_url'] is not None):
#     st.dataframe(data=st.session_state['data_from_url'].table)
    
    
show_all_datasets = False # st.checkbox('Show all datasets available')
if show_all_datasets == True:
    st.dataframe(data=data_catalog)
    
with expander_container:
    st.dataframe(data=selected_rows)

logger.debug(f"Done with rendering dataframe")