import streamlit as st
import math
import pandas as pd
import logging

import openpolicedata as opd

NA_DISPLAY_VALUE = "NOT APPLICABLE"
ALL = "ALL"

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

if 'last_selection' not in st.session_state:
    st.session_state['last_selection'] = None
    
@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    df = df.sort_values(by=["State","SourceName","TableType"])
    return df

@st.cache_data(show_spinner="Loading year information...")
def get_years(selectbox_sources, selectbox_states, selectbox_table_types):
    src = opd.Source(selectbox_sources, state=selectbox_states)
    years = src.get_years(table_type=selectbox_table_types, force=True)
    years.sort(reverse=True)
    logger.debug(f"Updated years to {years}")
    return [str(x) if x!=opd.defs.NA else NA_DISPLAY_VALUE for x in years]

@st.cache_data(show_spinner="Loading agency information...")
def get_agencies(selectbox_sources, selectbox_states, selectbox_table_types, year):
    src = opd.Source(selectbox_sources, state=selectbox_states)
    agencies = src.get_agencies(table_type=selectbox_table_types, year=year)
    agencies.sort()
    agencies.insert(0, ALL)
    return agencies


data_catalog = get_data_catalog()
st.title('Open Police Data')


st.subheader('Selected Dataset Details')
expander_container = st.container()

with st.sidebar:
    st.header('Dataset Filters')
    selectbox_states = st.selectbox('States', data_catalog['State'].unique(), 
                                    help='Select a state to filter by')
    logger.debug(f"selectbox_states = {selectbox_states}")
    if len(selectbox_states) == 0:
        selected_rows = data_catalog.copy()
    else:
        selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]

    selectbox_sources = st.selectbox('Available Sources', selected_rows['SourceName'].unique(), 
                                     help='Select a source')

    if len(selectbox_sources) > 0:    
        selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]

    selectbox_table_types = st.selectbox('Available Table Types', selected_rows['TableType'].unique(), 
                                         help='Select a table type')

    if len(selectbox_table_types) > 0:       
        selected_rows = selected_rows[selected_rows['TableType'].isin(
            [selectbox_table_types])]

    years = get_years(selectbox_sources, selectbox_states, selectbox_table_types)

    selectbox_years = st.selectbox('Available Years', years, 
                                   help='Select a year')
    
    selectbox_agencies = None
    if len(selectbox_years) > 0:
        selected_year = selectbox_years if selectbox_years!=NA_DISPLAY_VALUE else opd.defs.NA
        selected_year = int(selected_year) if selected_year.isdigit() else selected_year
        logger.debug(f"Selected year is {selected_year} with type {type(selected_year)}")
        matches = selected_rows['Year'] == selected_year
        if matches.any():
            selected_rows = selected_rows[matches]
            logger.debug(f"selectbox_years != 0, selected_rows = {selected_rows}")
        else:
            selected_rows = selected_rows[selected_rows['Year']==opd.defs.MULTI]
            if len(selected_rows)>1:
                logger.debug("Number of multi-rows is >1")
                start_years = selected_rows["coverage_start"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                end_years = selected_rows["coverage_end"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                all_years = [range(x,y+1) if pd.notnull(x) and pd.notnull(y) else pd.NA for x,y in zip(start_years, end_years)]
                tf = [selected_year in y if pd.notnull(y) else False for y in all_years]
                selected_rows = selected_rows[tf]

        if selected_rows.iloc[0]["Agency"]==opd.defs.MULTI and selected_rows.iloc[0]["DataType"] not in ["CSV","Excel"]:
            agencies = get_agencies(selectbox_sources, selectbox_states, selectbox_table_types, selected_rows.iloc[0]["Year"])
            selectbox_agencies = st.selectbox('Available Agencies', agencies, 
                                   help='Select an agency')


new_selection = [selectbox_states, selectbox_sources, selectbox_table_types, selectbox_years, selectbox_agencies]
logger.debug(f"Old selection = {st.session_state['last_selection']}")
logger.debug(f"New selection = {new_selection}")
if st.session_state['last_selection'] != new_selection:
    logger.debug("Resetting download button")
    st.session_state['show_download'] = False
    st.session_state['csv_text_output'] = None
    st.session_state['preview'] = None
    st.session_state['last_selection'] = new_selection

collect_help = "This collects the data from the data source such as a URL and will make it ready for download. This may take some time."

agency_filter = None
agency_name = selected_rows.iloc[0]["Agency"]
if selectbox_agencies is not None and selectbox_agencies!=ALL:
    agency_filter = selectbox_agencies
    agency_name = selectbox_agencies

logger.debug(f"Agency name is {agency_name} and agency filter is {agency_filter}")

with st.empty():
    if not st.session_state['show_download'] and st.button('Collect data', help=collect_help):
        logger.debug(f'***source_name={selectbox_sources}, state={selectbox_states}')
        src = opd.Source(source_name=selectbox_sources, state=selectbox_states)        
        logger.debug("Downloading data from URL")
        logger.debug(f"Table type is {selectbox_table_types} and year is {selected_year}")

        record_count = None
        if selected_rows.iloc[0]["DataType"] not in ["CSV","Excel"]:
            with st.spinner("Retrieving record count..."):
                record_count = src.get_count(year=selected_year, table_type=selectbox_table_types, agency=agency_filter)

        wait_text = "Retrieving Data..."
        no_data_str = f"No data found for the {selectbox_table_types} table for {selectbox_sources} in {selected_year}"
        no_data_str = f"{no_data_str} when filtering for agency {agency_filter}"
        if record_count is None:
            with st.spinner(wait_text):
                data_from_url = src.load_from_url(year=selected_year, table_type=selectbox_table_types, agency=agency_filter).table

            if len(data_from_url)==0:
                st.write(no_data_str)
        else:
            df_list = []
            batch_size = 5000
            nbatches = math.ceil(record_count / batch_size)
            pbar = st.progress(0, text=wait_text)
            iter = 0
            for tbl in src.load_from_url_gen(year=selected_year, table_type=selectbox_table_types, nbatch=batch_size, agency=agency_filter):
                iter+=1
                df_list.append(tbl.table)
                pbar.progress(iter / nbatches, text=wait_text)
                
            if len(df_list)==0:
                st.write(no_data_str)
                data_from_url = []
            else:
                data_from_url = pd.concat(df_list)

        if len(data_from_url)>0:
            logger.debug(f"Data downloaded from URL. Total of {len(data_from_url)} rows")
            csv_text = data_from_url.to_csv(index=False)
            csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
            st.session_state['csv_text_output'] = csv_text_output
            #st.dataframe(data=selected_rows)
            st.session_state['show_download'] = True
            logger.debug(f"csv_text_output len is {len(csv_text_output)}  type(csv_text_output) = {type(csv_text_output)}")

    if st.session_state['show_download']:
        csv_filename = opd.data.get_csv_filename(selected_rows.iloc[0]["State"], selected_rows.iloc[0]["SourceName"], agency_name , selected_rows.iloc[0]["TableType"], selected_year)
        logger.debug(f"csv_filename = {csv_filename}")
        if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name=csv_filename, mime='text/csv'):
            logger.debug('Download complete!!!!!')
    
with expander_container:
    st.dataframe(data=selected_rows)

if st.session_state["preview"] is not None:
    st.divider()
    st.subheader("Preview")
    st.dataframe(data=st.session_state["preview"])

logger.debug(f"Done with rendering dataframe")