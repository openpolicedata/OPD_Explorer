import streamlit as st
import argparse
from datetime import datetime
import logging
import math
from packaging import version
import pandas as pd
import re

from streamlit_logger import create_logger, get_remote_ip, Code
import openpolicedata as opd

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true')
args = parser.parse_args()
level = logging.DEBUG if args.debug else logging.INFO

__version__ = "1.1"

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

if 'logger' not in st.session_state:
    st.session_state['logger'] = create_logger(name = 'opd-app', level = level)
logger = st.session_state['logger']

if args.debug:
    logger.info("***********DEBUG MODE*************")

now = datetime.now()

logger.info(now)
logger.info("VERSIONS:")
logger.info(f"\tOpenPoliceData: {opd.__version__}")
logger.info(f"\tOPD Explorer: {__version__}")
logger.info(f"IP: {get_remote_ip()}")

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

load_failure = False

# Populate sidebar with dropdown menus and get selected dataset
with st.sidebar:
    st.header('Dataset Filters')
    selectbox_states = st.selectbox('States', data_catalog['State'].unique(), 
                                    help='Select a state to filter by')
    logger.info(f"Selected State: {selectbox_states}")
    selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]

    selectbox_sources = st.selectbox('Available Sources', selected_rows['SourceName'].unique(), 
                                     help='Select a source')
    logger.info(f"Selected Source: {selectbox_sources}")

    selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]

    # Table types that may be split into multiple sub-tables
    split_tables = ["COMPLAINTS", "CRASHES", "OFFICER-INVOLVED SHOOTINGS","USE OF FORCE"]
    table_types = selected_rows['TableType'].unique()
    table_type_general = table_types.copy()
    table_types_sub = [None for _ in range(len(table_types))]
    for k,x in enumerate(table_types):
        for y in split_tables:
            m = re.search(y+"\s?-\s?(.+)", x)
            if m:
                table_type_general[k] = y
                table_types_sub[k] = m.group(1)
                break

    table_type_general_sort = list(set(table_type_general))
    table_type_general_sort.sort()
    selectbox_table_types = st.selectbox('Available Table Types', table_type_general_sort, 
                                         help='Select a table type (such as TRAFFIC STOPS or USE OF FORCE).\n\n'+
                                         'NOTE: Some datasets are split across multiple tables where unique IDs indicate related data between tables. '+
                                         "For example, a use of force dataset could have two tables: one for incident details and one for persons involved. "+
                                         "An incident ID could appear in both tables allowing the user to identify all persons involved in a particular incident.")
    logger.info(f"Selected table type: {selectbox_table_types}")

    related_tables = None
    # Selected table type has sub-tables
    m = [x==selectbox_table_types for x in table_type_general]
    table_types = [x for k,x in enumerate(table_types) if m[k]]
    selected_rows = selected_rows[selected_rows['TableType'].isin(table_types)]
    table_type_general = [x for k,x in enumerate(table_type_general) if m[k]]
    table_types_sub = [x for k,x in enumerate(table_types_sub) if m[k]]

    if all([x is not None for x in table_types_sub]):
        logger.code_reached(Code.SUBTABLE_MENU)
        selectbox_subtype = st.selectbox('Table Subcategory', table_types_sub, 
                                help=f'The {table_type_general[0]} dataset is split into the following tables that all may be of interest: '+
                                f'{table_types_sub}. They likely use unique IDs to enable finding related data across tables.')
        logger.info(f"Selected table subtype: {selectbox_subtype}")

        selected_table = [x for x,y in zip(table_types, table_types_sub) if y==selectbox_subtype][0]
        related_tables = [x for x,y in zip(table_types, table_types_sub) if y!=selectbox_subtype]
        selected_rows = selected_rows[selected_rows['TableType']==selected_table]
    else:
        logger.code_reached(Code.NO_SUBTABLE_MENU)
        selected_table = table_types[0]

    try:
        years = get_years(selectbox_sources, selectbox_states, selected_table)
    except:
        logger.exception('')
        load_failure = True

    if not load_failure:
        selectbox_years = st.selectbox('Available Years', years, 
                                    help='Select a year')
        logger.info(f"Selected year: {selectbox_years}")
        
        selectbox_agencies = None
        selected_year = selectbox_years if selectbox_years!=NA_DISPLAY_VALUE else opd.defs.NA
        selected_year = int(selected_year) if selected_year.isdigit() else selected_year
        matches = selected_rows['Year'] == selected_year
        if matches.any():
            if selected_year==opd.defs.NA:
                logger.code_reached(Code.NA_YEAR_DATA)
            else:
                logger.code_reached(Code.SINGLE_YEAR_DATA)
            selected_rows = selected_rows[matches]
        else:
            logger.code_reached(Code.MULTIYEAR_DATA)
            selected_rows = selected_rows[selected_rows['Year']==opd.defs.MULTI]
            if len(selected_rows)>1:
                logger.code_reached(Code.MULTIPLE_MULTIYEAR_DATA)
                logger.debug("Number of multi-rows is >1")
                start_years = selected_rows["coverage_start"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                end_years = selected_rows["coverage_end"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                all_years = [range(x,y+1) if pd.notnull(x) and pd.notnull(y) else pd.NA for x,y in zip(start_years, end_years)]
                tf = [selected_year in y if pd.notnull(y) else False for y in all_years]
                selected_rows = selected_rows[tf]

        if selected_rows.iloc[0]["Agency"]==opd.defs.MULTI and selected_rows.iloc[0]["DataType"] not in ["CSV","Excel"]:
            try:
                agencies = get_agencies(selectbox_sources, selectbox_states, selected_table, selected_rows.iloc[0]["Year"])
                logger.code_reached(Code.GET_AGENCIES)
            except:
                logger.exception('')
                load_failure = True
            if not load_failure:
                selectbox_agencies = st.selectbox('Available Agencies', agencies, 
                                    help='Select an agency')
                logger.info(f"Selected agency: {selectbox_agencies}")

failure_msg = "The requested dataset information cannot be loaded due to an error. The error is likely caused by "+\
                "an error with the police department or agency site that the data is sourced from. " +\
                "If this error is with the agency's site, you can still access other datasets from OPD Explorer.\n\n" + \
                "If you need to access to the currently selected dataset, please try again later or contact us on our " +\
                "[discussion board](https://github.com/openpolicedata/openpolicedata/discussions) or by [email](mailto:openpolicedata@gmail.com)."
if load_failure:
    st.error(failure_msg)
else:
    # Display information on selected table
    map = {
            "State":"State",
            "SourceName":"Source",
            "AgencyFull":"Full Agency Name",
            "TableType":"Table Type",
            "coverage_start":"Coverage Start",
            "coverage_end":"Coverage End (Est.)",
            "source_url":"Source URL",
            "readme":"Data Dictionary URL",
        }
    ds = selected_rows.rename(columns=map)
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
    ds["Data Dictionary URL"] = "No direct URL recorded. Check Source URL." \
        if pd.isnull(ds["Data Dictionary URL"]) else ds["Data Dictionary URL"]
    text=""
    for idx in ds.index:
        text+=f"**{idx}**: {ds[idx]}  \n"
    st.info(text)

    new_selection = [selectbox_states, selectbox_sources, selected_table, selectbox_years, selectbox_agencies]
    if st.session_state['last_selection'] != new_selection:
        # New selection. Delete previously downloaded data
        logger.code_reached(Code.CHANGE_SELECTION)
        logger.info("Resetting download button")
        st.session_state['csv_text_output'] = None
        st.session_state['preview'] = None
        st.session_state['last_selection'] = new_selection

    collect_help = "This collects the data from the data source's URL. Upon completion, the data will be available for download. This may take some time."

    agency_filter = None
    agency_name = selected_rows.iloc[0]["Agency"]
    if selectbox_agencies is not None and selectbox_agencies!=ALL:
        logger.code_reached(Code.SINGLE_AGENCY_SELECT)
        agency_filter = selectbox_agencies
        agency_name = selectbox_agencies

    if related_tables is not None:
        st.markdown(f'*Related tables*: {",".join(related_tables)}' )

    with st.empty():
        if not load_failure and st.session_state["preview"] is None and st.button('Retrieve data', help=collect_help):
            src = opd.Source(source_name=selectbox_sources, state=selectbox_states)        
            logger.info("Downloading data from URL")

            record_count = None
            if selected_rows.iloc[0]["DataType"] not in ["CSV","Excel"]:
                wait_text = "Retrieving Data..."
                with st.spinner("Retrieving record count..."):
                    try:
                        record_count = src.get_count(year=selected_year, table_type=selected_table, agency=agency_filter)
                        logger.info(f"record_count: {record_count}")
                        logger.code_reached(Code.FETCH_DATA_GET_COUNT)
                    except:
                        logger.exception('')
                        load_failure = True
            else:
                wait_text = "Retrieving Data... (Large datasets may take time to retrieve)"

            no_data_str = f"No data found for the {selected_table} table for {selectbox_sources} in {selected_year}"
            if agency_filter is not None:
                no_data_str = f"{no_data_str} when filtering for agency {agency_filter}"
            if not load_failure and record_count is None:
                with st.spinner(wait_text):
                    try:
                        data_from_url = src.load_from_url(year=selected_year, table_type=selected_table, agency=agency_filter).table
                        logger.code_reached(Code.FETCH_DATA_LOAD_WO_COUNT)
                    except:
                        logger.exception('')
                        load_failure = True

                if not load_failure and len(data_from_url)==0:
                    st.write(no_data_str)
            elif not load_failure:
                df_list = []
                batch_size = 5000
                nbatches = math.ceil(record_count / batch_size)
                pbar = st.progress(0, text=wait_text)
                iter = 0
                try:
                    for tbl in src.load_from_url_gen(year=selected_year, table_type=selected_table, nbatch=batch_size, agency=agency_filter):
                        iter+=1
                        df_list.append(tbl.table)
                        pbar.progress(iter / nbatches, text=wait_text)
                    logger.code_reached(Code.FETCH_DATA_LOAD_WITH_COUNT)
                except:
                    logger.exception('')
                    load_failure = True
                    
                if not load_failure:
                    if len(df_list)==0:
                        st.write(no_data_str)
                        data_from_url = []
                    else:
                        data_from_url = pd.concat(df_list)

            if load_failure:
                st.error(failure_msg)
            elif len(data_from_url)>0:
                logger.info(f"Data downloaded from URL. Total of {len(data_from_url)} rows")
                # Replace non-ASCII characters with '' because st.dataframe will throw an error otherwise
                p = data_from_url.head(20)
                try:
                    p = p.replace({r'[^\x00-\x7F]+':''}, regex=True)
                    logger.code_reached(Code.PREVIEW_REGEXREP_SUCCESS)
                except:
                    pass
                st.session_state['preview'] = p
                st.session_state["record_count"] = len(data_from_url)
                csv_text = data_from_url.to_csv(index=False)
                csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
                st.session_state['csv_text_output'] = csv_text_output
            else:
                logger.info("No data found")

        if st.session_state["preview"] is not None:
            # Replace progress bar with number of records
            st.markdown(f'*Total Number of Records*: {st.session_state["record_count"]}' )

    if st.session_state["preview"] is not None:
        csv_filename = opd.data.get_csv_filename(selected_rows.iloc[0]["State"], selected_rows.iloc[0]["SourceName"], 
                                                agency_name , selected_rows.iloc[0]["TableType"], selected_year)
        if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name=csv_filename, mime='text/csv'):
            logger.info('Download complete!!!!!')
            logger.code_reached(Code.DOWNLOAD)

        st.divider()
        st.subheader("Preview")
        st.dataframe(data=st.session_state["preview"])
    else:
        st.divider()
        # Add some space
        for _ in range(0):
            st.text("  ")

    st.info("Questions or Suggestions? Please reach out to us on our "
            "[discussion board](https://github.com/openpolicedata/openpolicedata/discussions) or by [email](openpolicedata@gmail.com).\n\n"+
            "NOTE: All data is downloaded directly from the source and is not altered in any way. "+
            "Column names and codes may be difficult to understand. Check the data dictionary and "+
            "source URLs for more information. If you still are having issues, feel free to reach out to us at the link above.")

logger.log_coverage()
logger.info(f'Done with rendering dataframe using OPD Version {opd.__version__}')
