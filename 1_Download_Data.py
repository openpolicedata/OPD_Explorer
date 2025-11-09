import streamlit as st
import argparse
from datetime import datetime
import logging
import pandas as pd
import re

from streamlit_logger import Code
import load_data
import openpolicedata as opd

# Must add -- before arguments so that streamlit does not try to read our args
# i.e. -- --debug
# https://discuss.streamlit.io/t/command-line-arguments/386/4
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true')
args = parser.parse_args()
level = logging.DEBUG if args.debug else logging.INFO

NA_DISPLAY_VALUE = "NOT APPLICABLE"
ALL = "ALL"

load_failure = False
selection = {}
msgs = {}

logger = st.session_state['logger']

now = datetime.now()

api_data_types = ["ArcGIS",'Carto','CKAN','Socrata']

@st.cache_data(show_spinner="Loading year information...")
def get_years(selectbox_sources, selectbox_states, selectbox_table_types, selected_agency):
    src = opd.Source(selectbox_sources, state=selectbox_states, agency=selected_agency)
    years = src.get_years(table_type=selectbox_table_types, force=False)
    years.sort(reverse=True)
    return [str(x) if x!=opd.defs.NA else NA_DISPLAY_VALUE for x in years]

@st.cache_data(show_spinner="Loading agency information...")
def get_agencies(selectbox_sources, selectbox_states, selectbox_table_types, year, selected_agency,
                 url_contains, id_contains):
    src = opd.Source(selectbox_sources, state=selectbox_states, agency=selected_agency)
    agencies = src.get_agencies(table_type=selectbox_table_types, year=year, url=url_contains, id=id_contains)
    agencies.sort()
    agencies.insert(0, ALL)
    return agencies


data_catalog = st.session_state['data_catalog']

# Create columns to center text
st.markdown("Find Dataset ➡️ Retrieve Data ➡️ Download CSV")

st.subheader('Selected Dataset Details')

# Populate sidebar with dropdown menus and get selected dataset
with st.sidebar:
    st.header('Dataset Filters')
    selectbox_states = st.selectbox('States', data_catalog['State'].unique(), 
                                    help="Select a state to filter by. MULTIPLE indicates datasets that contain more than 1 state's data")
    logger.debug(f"Selected State: {selectbox_states}")
    selected_rows = data_catalog[data_catalog['State']==selectbox_states]

    selectbox_sources = st.selectbox('Available Sources', selected_rows['SourceName'].unique(), 
                                     help="Select a source (typically a police department, sheriff's office, "
                                     "or a state (if data is for all agencies in a state))")
    logger.debug(f"Selected Source: {selectbox_sources}")

    selected_rows = selected_rows[selected_rows['SourceName']==selectbox_sources]

    # Table types that may be split into multiple sub-tables
    split_tables = ["COMPLAINTS", "CRASHES", "OFFICER-INVOLVED SHOOTINGS","USE OF FORCE"]
    table_types = selected_rows['TableType'].unique()
    table_type_general = table_types.copy()
    table_types_sub = [None for _ in range(len(table_types))]
    for k,x in enumerate(table_types):
        for y in split_tables:
            m = re.search(y+r"\s?-\s?(.+)", x)
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
    logger.debug(f"Selected table type: {selectbox_table_types}")

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
        logger.debug(f"Selected table subtype: {selectbox_subtype}")

        selection['table'] = [x for x,y in zip(table_types, table_types_sub) if y==selectbox_subtype][0]
        related_tables = [x for x,y in zip(table_types, table_types_sub) if y!=selectbox_subtype]
        selected_rows = selected_rows[selected_rows['TableType']==selection['table']]
    else:
        logger.code_reached(Code.NO_SUBTABLE_MENU)
        selection['table'] = table_types[0]

    all_agencies_for_source = selected_rows['Agency'].unique()
    if len(all_agencies_for_source)>1:
        # The data source table contains multiple agency options for this source
        # Usually, this occurs for counties where there is data for the county agency, 
        # such as the county sheriff, and for all agencies in the county (i.e. agency = MULTIPLE)
        selected_agency = st.selectbox('Available Agencies', all_agencies_for_source, 
                                    help='Select an agency (MULTIPLE indicates multiple agencies within the limits of the source location)')
        selected_rows = selected_rows[selected_rows['Agency'].isin(
            [selected_agency])]
        logger.code_reached(Code.MULTIPLE_AGENCIES_IN_TABLE)
    else:
        selected_agency = all_agencies_for_source[0]
        logger.code_reached(Code.SINGLE_AGENCY_IN_TABLE)

    try:
        years = get_years(selectbox_sources, selectbox_states, selection['table'], selected_agency)
    except:
        logger.exception('')
        load_failure = True

    if not load_failure:
        load_file =  len(selected_rows) == 1 and selected_rows.iloc[0]["DataType"] not in api_data_types and \
            selected_rows.iloc[0]['Year']==opd.defs.MULTI
        if load_file:
            logger.debug("Single file load mode")
            # Data is a single file. Since the whole file has to be loaded, just let the user download
            # all years at once
            years = [f"{min(years)}-{max(years)}"]

        selectbox_years = st.selectbox('Available Years', years, 
                                    help='Select a year')
        logger.debug(f"Selected year: {selectbox_years}")
        
        selectbox_agencies = None
        selectbox_coverage = None
        selection['year'] = selectbox_years if selectbox_years!=NA_DISPLAY_VALUE else opd.defs.NA
        selection['year'] = int(selection['year']) if selection['year'].isdigit() else selection['year']
        matches = selected_rows['Year'] == selection['year']
        if matches.any():
            if selection['year']==opd.defs.NA:
                logger.code_reached(Code.NA_YEAR_DATA)
            else:
                logger.code_reached(Code.SINGLE_YEAR_DATA)
            selected_rows = selected_rows[matches]
        else:
            if load_file:
                logger.code_reached(Code.MULTIYEAR_FILE)
                orig_year = selection['year']
                selection['year'] = opd.defs.MULTI
            else:
                logger.code_reached(Code.MULTIYEAR_DATA)
            selected_rows = selected_rows[selected_rows['Year']==opd.defs.MULTI]
            if len(selected_rows)>1:
                logger.code_reached(Code.MULTIPLE_MULTIYEAR_DATA)
                logger.debug("Number of multi-rows is >1")
                start_years = selected_rows["coverage_start"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                end_years = selected_rows["coverage_end"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                all_years = [range(x,y+1) if pd.notnull(x) and pd.notnull(y) else pd.NA for x,y in zip(start_years, end_years)]
                tf = [selection['year'] in y if pd.notnull(y) else False for y in all_years]

                if not any(tf) and selection['year']==now.year and any([x+1==selection['year'] for x in end_years]):
                    # Source table has not been updated for current year but dataset has data for current year
                    tf = [x+1==selection['year'] for x in end_years]

                selected_rows = selected_rows[tf]

                if len(selected_rows)>1:
                    # There are multiple multi-year datasets that include the selected year
                    start_years = selected_rows["coverage_start"].dt.strftime('%Y-%m-%d').to_list()
                    end_years =   selected_rows["coverage_end"].dt.strftime('%Y-%m-%d').to_list()

                    coverage = [f"{x} - {y}" for x,y in zip(start_years, end_years)]
                    selectbox_coverage = st.selectbox('Select dataset date range to request selected year from', coverage, 
                                    help='Multiple datasets have been identified containing the selected year. Select a data range to specify a specific/single dataset.')
                    
                    selected_rows = selected_rows[[x==selectbox_coverage for x in coverage]]
                    logger.code_reached(Code.MULTIPLE_MULTIYEAR_DATA_OVERLAP)


        if selected_rows.iloc[0]["Agency"]==opd.defs.MULTI and selected_rows.iloc[0]["DataType"] in api_data_types:
            try:
                agencies = get_agencies(selectbox_sources, selectbox_states, selection['table'], selected_rows.iloc[0]["Year"], selected_agency,
                                        selected_rows.iloc[0]["URL"], selected_rows.iloc[0]["dataset_id"])
                logger.code_reached(Code.GET_AGENCIES)
            except:
                logger.exception('')
                load_failure = True
            if not load_failure:
                selectbox_agencies = st.selectbox('Available Agencies', agencies, 
                                    help='Select an agency')
                logger.debug(f"Selected agency: {selectbox_agencies}")

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

    new_selection = [selectbox_states, selectbox_sources, selection['table'], selectbox_years, selectbox_agencies, selected_agency, selectbox_coverage]
    if st.session_state['last_selection'] != new_selection:
        # New selection. Delete previously downloaded data
        logger.code_reached(Code.CHANGE_SELECTION)
        logger.debug("Resetting download button")
        st.session_state['csv_text_output'] = None
        st.session_state['preview'] = None
        st.session_state['last_selection'] = new_selection

    collect_help = "This collects the data from the data source's URL. Upon completion, the data will be available for download "+\
                   "using the *Download CSV button*. This may take some time."

    selection['agency'] = None
    agency_name = selected_rows.iloc[0]["Agency"]
    if selectbox_agencies is not None and selectbox_agencies!=ALL:
        logger.code_reached(Code.SINGLE_AGENCY_SELECT)
        selection['agency'] = selectbox_agencies
        agency_name = selectbox_agencies
    else:
        logger.code_reached(Code.SINGLE_AGENCY_DATA)

    if related_tables is not None:
        st.markdown(f'*Related tables*: {",".join(related_tables)}' )

    with st.empty():
        if not load_failure and st.session_state["preview"] is None and st.button('Retrieve data', help=collect_help):
            src = opd.Source(source_name=selectbox_sources, state=selectbox_states, agency=selected_agency)        
            logger.info(f"Begininng data download from URL for {selectbox_sources=}, {selectbox_states=}, {selected_agency=}")

            record_count = None
            if selected_rows.iloc[0]["DataType"] in api_data_types:
                msgs['wait'] = "Retrieving Data..."
                with st.spinner("Retrieving record count..."):
                    try:
                        logger.info(f"Getting count for {selection['year']=}, {selection['table']=}, {selection['agency']=}, "+\
                                    f'{selected_rows.iloc[0]["URL"]=}, {selected_rows.iloc[0]["dataset_id"]=}')
                        record_count = src.get_count(year=selection['year'], table_type=selection['table'], agency=selection['agency'],
                                                     url=selected_rows.iloc[0]["URL"], 
                                                     id=selected_rows.iloc[0]["dataset_id"])
                        logger.info(f"record_count: {record_count}")
                        logger.code_reached(Code.FETCH_DATA_GET_COUNT)
                    except Exception as e:
                        logger.exception('Exception encountered during get_count', exc_info=e)
                        load_failure = True
            else:
                msgs['wait'] = "Retrieving Data... (Large datasets may take time to retrieve)"

            msgs['no_data'] = f"No data found for the {selection['table']} table for {selectbox_sources} in {selection['year']}"
            if selection['agency'] is not None:
                msgs['no_data'] = f"{msgs['no_data']} when filtering for agency {selection['agency']}"

            if not load_failure:
                data_as_csv_txt, nrows, df_prev, load_failure = load_data.load(src, selection, selected_rows, record_count, msgs)

            if load_failure:
                st.error(failure_msg)
            elif nrows>0:
                logger.info(f"Data downloaded from URL. Total of {nrows} rows")
                st.session_state['preview'] = df_prev
                st.session_state["record_count"] = nrows
                st.session_state['csv_text_output'] = data_as_csv_txt
            else:
                st.write(msgs['no_data'])
                logger.info("No data found")

        if st.session_state["preview"] is not None:
            # Replace progress bar with number of records
            st.markdown(f'*Total Number of Records*: {st.session_state["record_count"]}' )

    if st.session_state["preview"] is not None:
        csv_filename = opd.data.get_csv_filename(selected_rows.iloc[0]["State"], selected_rows.iloc[0]["SourceName"], 
                                                agency_name , selected_rows.iloc[0]["TableType"], orig_year if load_file else selection['year'])
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

st.session_state['is_starting_up'] = False