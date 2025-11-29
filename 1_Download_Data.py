import streamlit as st
from datetime import datetime
import logging
import pandas as pd
from urllib.parse import urlparse

import dashboard_utils
import utils
from init import clear_defaults
import openpolicedata as opd

# TODO: UPDATE COVERAGE

load_failure = False
selection = {}
msgs = {}

logger = st.session_state['logger']

now = datetime.now()

api_data_types = ["ArcGIS",'Carto','CKAN','Socrata']

data_catalog = st.session_state['data_catalog']

# Create columns to center text
st.markdown("Find Dataset ➡️ Retrieve Data ➡️ Download CSV")

st.subheader('Selected Dataset Details')

defaults = st.session_state['default']['download']

# Populate sidebar with dropdown menus and get selected dataset
with st.sidebar:
    st.header('Dataset Filters')

    states = data_catalog['State'].unique()
    default_state = dashboard_utils.get_default('state', states, defaults)
    selectbox_states = st.selectbox('States', states, 
                                    index=default_state,
                                    on_change=clear_defaults,
                                    args=['download', 'state'],
                                    help="Select a state to filter by. MULTIPLE indicates datasets that contain more than 1 state's data")
    logger.debug(f"Selected State: {selectbox_states}")
    selected_rows = data_catalog[data_catalog['State']==selectbox_states]

    sources = selected_rows['SourceName'].unique()
    default_source = dashboard_utils.get_default('source', sources, defaults)
    selectbox_sources = st.selectbox('Sources', sources, 
                                     index=default_source,
                                     on_change=clear_defaults,
                                     args=['download', 'source'],
                                     help="Select a source (typically a police department, sheriff's office, "
                                     "or a state (if data is for all agencies in a state))")
    logger.debug(f"Selected Source: {selectbox_sources}")

    selected_rows = selected_rows[selected_rows['SourceName']==selectbox_sources]

    table_types = selected_rows['TableType'].unique()
    table_type_general, table_type_general_sort, table_types_sub = utils.split_tables(table_types)

    default_table_type_general = dashboard_utils.get_default('table_type_general', table_type_general_sort, defaults)
    selectbox_table_types = st.selectbox('Table Types', table_type_general_sort, 
                                         index=default_table_type_general,
                                         on_change=clear_defaults,
                                         args=['download', 'table_type_general'],
                                         help='Select a table type (such as TRAFFIC STOPS or USE OF FORCE).\n\n'+
                                         'NOTE: Some datasets are split across multiple tables where unique IDs indicate related data between tables. '+
                                         "For example, a use of force dataset could have two tables: one for incident details and one for persons involved. "+
                                         "An incident ID could appear in both tables allowing the user to identify all persons involved in a particular incident.")
    logger.debug(f"Selected table type: {selectbox_table_types}")

    # Reduces lists based on selection
    m = [x==selectbox_table_types for x in table_type_general]  # Matches
    table_types = [x for k,x in enumerate(table_types) if m[k]]
    table_type_general = [x for k,x in enumerate(table_type_general) if m[k]]
    table_types_sub = [x for k,x in enumerate(table_types_sub) if m[k]]

    selected_rows = selected_rows[selected_rows['TableType'].isin(table_types)]

    related_tables = None
    if all([x is not None for x in table_types_sub]):
        # Selected table type has sub-tables

        default_table_type_sub = dashboard_utils.get_default('table_type_sub', table_types_sub, defaults)
        selectbox_subtype = st.selectbox('Table Subcategory', table_types_sub, 
                                index=default_table_type_sub,
                                on_change=clear_defaults,
                                args=['download', 'table_type_sub'],
                                help=f'The {table_type_general[0]} dataset is split into the following tables that all may be of interest: '+
                                f'{table_types_sub}. They likely use unique IDs to enable finding related data across tables.')
        logger.debug(f"Selected table subtype: {selectbox_subtype}")

        selection['table'] = [x for x,y in zip(table_types, table_types_sub) if y==selectbox_subtype][0]
        related_tables = [x for x,y in zip(table_types, table_types_sub) if y!=selectbox_subtype]
        selected_rows = selected_rows[selected_rows['TableType']==selection['table']]
    else:
        selection['table'] = table_types[0]

    all_agencies_for_source = selected_rows['Agency'].unique()
    if len(all_agencies_for_source)>1:
        # The data source table contains multiple agency options for this source
        # Usually, this occurs for counties where there is data for the county agency, 
        # such as the county sheriff, and for all agencies in the county (i.e. agency = MULTIPLE)
        default_agency = dashboard_utils.get_default('agency', all_agencies_for_source, defaults)
        selected_agency = st.selectbox('Agencies', all_agencies_for_source, 
                                    index=default_agency,
                                    on_change=clear_defaults,
                                    args=['download', 'agency'],
                                    help='Select an agency (MULTIPLE indicates multiple agencies within the limits of the source location)')
        selected_rows = selected_rows[selected_rows['Agency'].isin(
            [selected_agency])]
    else:
        selected_agency = all_agencies_for_source[0]

    try:
        years = dashboard_utils.get_years(selectbox_sources, selectbox_states, selection['table'], selected_agency)
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
            default_year = 0
        else:
            default_year = dashboard_utils.get_default('year', years, defaults)

        selectbox_years = st.selectbox('Years', years, 
                                    index=default_year,
                                    on_change=clear_defaults,
                                    args=['download', 'year'],
                                    help='Select a year')
        logger.debug(f"Selected year: {selectbox_years}")
        
        selectbox_agencies = None
        selectbox_coverage = None
        selection['year'] = selectbox_years if selectbox_years!=utils.NA_DISPLAY_VALUE else opd.defs.NA  # Revert NA_DISPLAY_VALUE to NA if applicable
        selection['year'] = int(selection['year']) if selection['year'].isdigit() else selection['year']
        matches = selected_rows['Year'] == selection['year']
        if matches.any():
            # Year is a single year or NA
            selected_rows = selected_rows[matches]
        else:
            # Year is multi
            if load_file:
                # Data not accessed by API
                orig_year = selection['year']
                selection['year'] = opd.defs.MULTI
                
            selected_rows = selected_rows[selected_rows['Year']==opd.defs.MULTI]
            if len(selected_rows)>1:
                logger.debug("More than one datasets with Year=MULTIPLE")

                # Create list of years from coverage information in source table
                start_years = selected_rows["coverage_start"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                end_years = selected_rows["coverage_end"].apply(lambda x: int(x.year) if pd.notnull(x) else x)
                all_years = [range(x,y+1) if pd.notnull(x) and pd.notnull(y) else pd.NA for x,y in zip(start_years, end_years)]

                # Check for selection in each list
                tf = [selection['year'] in y if pd.notnull(y) else False for y in all_years]

                if not any(tf) and selection['year']==now.year and any([x+1==selection['year'] for x in end_years]):
                    # Source table has not been updated for current year but dataset has data for current year
                    tf = [x+1==selection['year'] for x in end_years]

                selected_rows = selected_rows[tf]

                if len(selected_rows)>1:
                    unique_urls = utils.get_unique_urls(selected_rows['URL'], selected_rows['dataset_id'])

                    default_url=0
                    if defaults['url']!=0:
                        full_unique = f"{defaults['url']}: {defaults['id']}"
                        if full_unique in unique_urls:
                            default_url = full_unique
                        elif urlparse(defaults['url']).hostname in unique_urls or \
                            urlparse('https://'+defaults['url']).hostname in unique_urls:
                            default_url = urlparse(defaults['url']).hostname
                        else:
                            default_url = defaults['url']

                        default_url = dashboard_utils.get_default('URL', unique_urls, default_url)
                    
                    selectbox_url = st.selectbox(
                        'Multiple Options: Select URL+ID', unique_urls,
                        index=default_url,
                        help='In rare cases, there are multiple datasets matching the selected parameters. Select URL and/or dataset ID to uniquely specify dataset.'
                    )
                    
                    selected_rows = selected_rows[[x==selectbox_url for x in unique_urls]]


        if selected_rows.iloc[0]["Agency"]==opd.defs.MULTI and selected_rows.iloc[0]["DataType"] in api_data_types:
            try:
                agencies = dashboard_utils.get_agencies(selectbox_sources, selectbox_states, selection['table'], selected_rows.iloc[0]["Year"], selected_agency,
                                        selected_rows.iloc[0]["URL"], selected_rows.iloc[0]["dataset_id"])
            except:
                logger.exception('')
                load_failure = True
            if not load_failure:
                selectbox_agencies = st.selectbox('Agencies', agencies, 
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

    new_selection = [selected_rows.iloc[0]["URL"], selected_rows.iloc[0]["dataset_id"]]
    if st.session_state['last_selection'] != new_selection:
        # New selection. Delete previously downloaded data
        logger.debug("Resetting download button")
        st.session_state['csv_text_output'] = None
        st.session_state['preview'] = None
        st.session_state['last_selection'] = new_selection

    collect_help = "This collects the data from the data source's URL. Upon completion, the data will be available for download "+\
                   "using the *Download CSV button*. This may take some time."

    selection['agency'] = None
    agency_name = selected_rows.iloc[0]["Agency"]
    if selectbox_agencies is not None and selectbox_agencies!=utils.ALL:
        selection['agency'] = selectbox_agencies
        agency_name = selectbox_agencies

    if related_tables is not None:
        st.markdown(f'*Related tables*: {",".join(related_tables)}' )

    with st.empty():
        if not load_failure and st.session_state['preview'] is None and st.button('Retrieve Data', help=collect_help):
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
                    except Exception as e:
                        logger.exception('Exception encountered during get_count', exc_info=e)
                        load_failure = True
            else:
                msgs['wait'] = "Retrieving Data... (Large datasets may take time to retrieve)"

            msgs['no_data'] = f"No data found for the {selection['table']} table for {selectbox_sources} in {selection['year']}"
            if selection['agency'] is not None:
                msgs['no_data'] = f"{msgs['no_data']} when filtering for agency {selection['agency']}"

            if not load_failure:
                data_as_csv_txt, nrows, df_prev, load_failure = dashboard_utils.load(src, selection, selected_rows, record_count, msgs)

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

        if st.session_state['preview'] is not None:
            # Replace progress bar with number of records
            st.markdown(f'*Total Number of Records*: {st.session_state["record_count"]}' )

    if st.session_state['preview'] is not None:
        csv_filename = opd.data.get_csv_filename(selected_rows.iloc[0]["State"], selected_rows.iloc[0]["SourceName"], 
                                                agency_name , selected_rows.iloc[0]["TableType"], orig_year if load_file else selection['year'])
        if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name=csv_filename, mime='text/csv'):
            logger.info('Download complete!!!!!')

        st.divider()
        st.subheader("Preview")
        st.dataframe(data=st.session_state['preview'])
    else:
        st.divider()
        # Add some space
        for _ in range(0):
            st.text("  ")