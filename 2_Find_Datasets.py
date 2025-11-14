import re
import streamlit as st

data_catalog = st.session_state["data_catalog"]
selection = data_catalog

ALL = "---ALL---"

with st.sidebar:
    st.header('Dataset Filters')
    options = data_catalog['State'].unique()
    options_all = [ALL]
    options_all.extend(options)
    selectbox_states = st.selectbox('States', options_all, 
                                    help="Select a state to filter by. MULTIPLE indicates datasets that contain more than 1 state's data")
    
    if selectbox_states!=ALL:
        selection = selection[selection['State']==selectbox_states]

    options = selection['SourceName'].unique()
    options_all = [ALL]
    options_all.extend(options)
    selectbox_sources = st.selectbox('Available Sources', options_all, 
                                     help="Select a source (typically a police department, sheriff's office, "
                                     "or a state (if data is for all agencies in a state))")
    
    if selectbox_sources!=ALL:
        selection = selection[selection['SourceName']==selectbox_sources]

    # Table types that may be split into multiple sub-tables
    split_tables = ["COMPLAINTS", "CRASHES", "OFFICER-INVOLVED SHOOTINGS","USE OF FORCE"]
    table_types = selection['TableType'].unique()
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
    options_all = [ALL]
    options_all.extend(table_type_general_sort)
    selectbox_table_types = st.selectbox('Available Table Types', options_all, 
                                         help='Select a table type (such as TRAFFIC STOPS or USE OF FORCE)')
    
    if selectbox_table_types!=ALL:
        m = [x==selectbox_table_types for x in table_type_general]
        table_types = [x for k,x in enumerate(table_types) if m[k]]
        selection = selection[selection['TableType'].isin(table_types)]

# Prevent pyarrow errors when Streamlit displays table
selection.loc[:, 'Year'] = selection['Year'].astype(str)
selection.loc[:, 'dataset_id'] = selection['dataset_id'].astype(str)

event = st.dataframe(data=selection,
                     on_select="rerun",
                     selection_mode='single-row',
                     hide_index=True)