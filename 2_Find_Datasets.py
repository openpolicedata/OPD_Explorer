import streamlit as st

data_catalog = st.session_state["data_catalog"]
selection = data_catalog

print(f'{len(selection)=}')

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
        print(selection)

    options = data_catalog['SourceName'].unique()
    options_all = [ALL]
    options_all.extend(options)
    selectbox_sources = st.selectbox('Available Sources', options_all, 
                                     help="Select a source (typically a police department, sheriff's office, "
                                     "or a state (if data is for all agencies in a state))")
    
    if selectbox_sources!=ALL:
        selection = selection[selection['SourceName']==selectbox_sources]

st.dataframe(data=selection)