import streamlit as st
import math
from packaging import version
import pandas as pd
import logging

import openpolicedata as opd

st.set_page_config(
    page_title="OpenPoliceData",
    page_icon="🌃",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a Bug': "https://github.com/openpolicedata/OPD_Explorer/issues"
    }
)

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

if 'last_selection' not in st.session_state:
    st.session_state['last_selection'] = None
    
@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    # Remove min_version = -1 (not available in any version) or min_version > current version
    df = df[df["min_version"].apply(lambda x: 
                                    pd.isnull(x) or (x.strip()!="-1" and version.parse(opd.__version__) >= version.parse(x))
                                    )]
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
st.title('OpenPoliceData Explorer')
st.caption("Explorer uses the [OpenPoliceData](https://pypi.org/project/openpolicedata/) Python library to access 365 (and growing) "+
           "incident-level datasets from police departments around the United States "+
           "including traffic stops, use of force, and officer-involved shootings data.")

# Create columns to center text
st.markdown("Find Dataset ➡️ Retrieve Data ➡️ Download CSV")

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
    if st.session_state["preview"] is None and st.button('Retrieve data', help=collect_help):
        logger.debug(f'***source_name={selectbox_sources}, state={selectbox_states}')
        src = opd.Source(source_name=selectbox_sources, state=selectbox_states)        
        logger.debug("Downloading data from URL")
        logger.debug(f"Table type is {selectbox_table_types} and year is {selected_year}")

        record_count = None
        if selected_rows.iloc[0]["DataType"] not in ["CSV","Excel"]:
            with st.spinner("Retrieving record count..."):
                record_count = src.get_count(year=selected_year, table_type=selectbox_table_types, agency=agency_filter)

        logger.debug(f"record_count is {record_count}")

        wait_text = "Retrieving Data..."
        no_data_str = f"No data found for the {selectbox_table_types} table for {selectbox_sources} in {selected_year}"
        no_data_str = f"{no_data_str} when filtering for agency {agency_filter}"
        if record_count is None:
            with st.spinner(wait_text):
                data_from_url = src.load_from_url(year=selected_year, table_type=selectbox_table_types, agency=agency_filter).table

            if len(data_from_url)==0:
                logger.debug("Table is empty")
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
                logger.debug(f"Table is empty")
            else:
                data_from_url = pd.concat(df_list)
                logger.debug(f"Table size is {len(data_from_url)}")

        if len(data_from_url)>0:
            logger.debug(f"Data downloaded from URL. Total of {len(data_from_url)} rows")
            # Replace non-ASCII characters with '' because st.dataframe will throw an error otherwise
            p = data_from_url.head(20)
            try:
                p = p.replace({r'[^\x00-\x7F]+':''}, regex=True)
            except:
                pass
            st.session_state['preview'] = p
            st.session_state["record_count"] = len(data_from_url)
            csv_text = data_from_url.to_csv(index=False)
            csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
            st.session_state['csv_text_output'] = csv_text_output
            logger.debug(f"csv_text_output len is {len(csv_text_output)}  type(csv_text_output) = {type(csv_text_output)}")
        else:
            logger.debug("No data found")

    if st.session_state["preview"] is not None:
        # Replace progress bar with number of records
        st.markdown(f'*Total Number of Records*: {st.session_state["record_count"]}' )
    
with expander_container:
    map = {
            "State":"State",
            "SourceName":"Source",
            "AgencyFull":"Full Agency Name",
            "TableType":"Table Type",
            "coverage_start":"Coverage Start",
            "coverage_end":"Coverage End (Est.)",
            "source_url":"Source URL",
            "readme":"Dictionary URL",
        }
    ds = selected_rows.rename(columns=map)
    show_table = False
    if not show_table:
        ds = ds[map.values()].iloc[0]
        ds["Table Type"] = ds["Table Type"].title()
        if pd.isnull(ds["Full Agency Name"]):
            ds = ds.drop("Full Agency Name")
        no_date = pd.isnull(ds["Coverage Start"])
        ds["Coverage Start"] = ds["Coverage Start"].strftime(r"%B %d, %Y") \
            if not no_date else "N/A"
        no_date_str = "N/A" if no_date else "Present (Approx.)"
        ds["Coverage End (Est.)"] = ds["Coverage End (Est.)"].strftime(r"%B %d, %Y") \
            if pd.notnull(ds["Coverage End (Est.)"]) else no_date_str
        ds["Dictionary URL"] = "No direct URL recorded. Check Source URL." \
            if pd.isnull(ds["Dictionary URL"]) else ds["Dictionary URL"]
        text=""
        for idx in ds.index:
            text+=f"**{idx}**: {ds[idx]}  \n"
        st.info(text)
    else:
        st.dataframe(data=selected_rows)

if st.session_state["preview"] is not None:
    csv_filename = opd.data.get_csv_filename(selected_rows.iloc[0]["State"], selected_rows.iloc[0]["SourceName"], 
                                             agency_name , selected_rows.iloc[0]["TableType"], selected_year)
    if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name=csv_filename, mime='text/csv'):
        logger.debug('Download complete!!!!!')

    st.divider()
    st.subheader("Preview")
    st.dataframe(data=st.session_state["preview"])

logger.debug(f"Done with rendering dataframe")