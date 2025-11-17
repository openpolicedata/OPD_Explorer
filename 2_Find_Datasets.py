import openpolicedata as opd
import streamlit as st
import utils

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

    table_types = selection['TableType'].unique()
    table_type_general, table_type_general_sort, _ = utils.split_tables(table_types)

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
                     hide_index=True,
                     height='stretch',
                     key='dataframe_datasets')

st.session_state['displayed_datasets'] = selection

if len(event.selection['rows'])==0:
    disabled = True
    label = 'Click a Checkbox in Table'
else:
    disabled = False
    label = 'Go to Selected Dataset'

if st.button(label, disabled=disabled):
    if len(event.selection['rows'])>0:
        # Set dataset_selection so that download page can load it
        selected_ds = st.session_state['displayed_datasets'].iloc[event.selection['rows'][0]]

        st.session_state['default']['state'] = selected_ds['State']
        st.session_state['default']['source'] = selected_ds['SourceName']
        st.session_state['default']['table_type_general'], st.session_state['default']['table_type_sub'], _ = utils.split_tables(selected_ds['TableType'])
        st.session_state['default']['agency'] = selected_ds['Agency']
        src = opd.Source(st.session_state['default']['source'], 
                         state=st.session_state['default']['state'], 
                         agency=st.session_state['default']['agency'])
        st.session_state['default']['year'] = str(max(src.get_years(table_type=selected_ds['TableType'], force=False, datasets=selected_ds)))
        st.session_state['default']['url'] = selected_ds['URL']
        st.session_state['default']['id'] = selected_ds['dataset_id']

        print(st.session_state['default'])

        st.switch_page("1_Download_Data.py")

st.session_state['dataset_selection'] = None

