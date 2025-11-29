import openpolicedata as opd
import streamlit as st
import requests
import pandas as pd

import utils
from init import clear_defaults
import dashboard_utils

data_catalog = st.session_state["data_catalog"]
selection = data_catalog

defaults = st.session_state['default']['datasets']

with st.sidebar:
    st.header('Dataset Filters')
    options = data_catalog['State'].unique()
    options_all = [utils.ALL]
    options_all.extend(options)
    default_state = dashboard_utils.get_default('state', options_all, defaults)
    selectbox_states = st.selectbox('States', options_all, 
                                    index=default_state,
                                    on_change=clear_defaults,
                                    args=['datasets', 'state'],
                                    help="Select a state to filter by. MULTIPLE indicates datasets that contain more than 1 state's data")
    
    if selectbox_states!=utils.ALL:
        selection = selection[selection['State']==selectbox_states]

    options = selection['SourceName'].unique()
    options_all = [utils.ALL]
    options_all.extend(options)
    default_source = dashboard_utils.get_default('source', options_all, defaults)
    selectbox_sources = st.selectbox('Sources', options_all, 
                                     index=default_source,
                                     on_change=clear_defaults,
                                     args=['datasets', 'source'],
                                     help="Select a source (typically a police department, sheriff's office, "
                                     "or a state (if data is for all agencies in a state))")
    
    if selectbox_sources!=utils.ALL:
        selection = selection[selection['SourceName']==selectbox_sources]

    table_types = selection['TableType'].unique()
    table_type_general, table_type_general_sort, _ = utils.split_tables(table_types)

    options_all = [utils.ALL]
    options_all.extend(table_type_general_sort)
    default_table = dashboard_utils.get_default('table', options_all, defaults)
    selectbox_table_types = st.selectbox('Table Types', options_all, 
                                         index=default_table,
                                         on_change=clear_defaults,
                                         args=['datasets', 'table'],
                                         help='Select a table type (such as TRAFFIC STOPS or USE OF FORCE)')
    
    if selectbox_table_types!=utils.ALL:
        m = [x==selectbox_table_types for x in table_type_general]
        table_types = [x for k,x in enumerate(table_types) if m[k]]
        selection = selection[selection['TableType'].isin(table_types)]

st.subheader('Filtered Datasets')

# Prevent pyarrow errors when Streamlit displays table
selection.loc[:, 'Year'] = selection['Year'].astype(str)
selection.loc[:, 'dataset_id'] = selection['dataset_id'].astype(str)

event = st.dataframe(data=selection,
                     on_select="rerun",
                     selection_mode='single-row',
                     hide_index=True,
                     height='stretch',
                     key='dataframe_datasets')

if len(event.selection['rows'])==0:
    disabled = True
    label = 'Click a Checkbox in Table'
else:
    disabled = False
    label = 'Go to Selected Dataset'

if st.button(label, disabled=disabled):
    if len(event.selection['rows'])>0:
        # Go to Download page with selected filter
        selected_ds = selection.iloc[event.selection['rows'][0]]

        st.session_state['default']['download']['state'] = selected_ds['State']
        st.session_state['default']['download']['source'] = selected_ds['SourceName']
        st.session_state['default']['download']['table_type_general'], _, st.session_state['default']['download']['table_type_sub'] = utils.split_tables(selected_ds['TableType'])
        st.session_state['default']['download']['agency'] = selected_ds['Agency']
        src = opd.Source(st.session_state['default']['download']['source'], 
                         state=st.session_state['default']['download']['state'], 
                         agency=st.session_state['default']['download']['agency'])
        year = str(max(src.get_years(table_type=selected_ds['TableType'], force=False, datasets=selected_ds)))
        year = year if year!='NONE' else utils.NA_DISPLAY_VALUE
        st.session_state['default']['download']['year'] = year
        st.session_state['default']['download']['url'] = selected_ds['URL']
        st.session_state['default']['download']['id'] = selected_ds['dataset_id']

        print(st.session_state['default']['download'])

        st.switch_page("1_Download_Data.py")

npi_url = 'https://national.cpdp.co/'
if selectbox_sources==utils.ALL:
    if selectbox_states!=utils.ALL and selectbox_states!=opd.defs.MULTI:
        test_url = npi_url + 'states/' + selectbox_states.replace(' ','-')
        r = requests.get(test_url, timeout=3)
        try:
            r.raise_for_status()
            if 'placeholder="Search Data"' in r.text:
                npi_url = test_url  # URL contains placeholders for data because data exists
        except:
            pass
elif len(selection)>0:
    if selection['State'].nunique()==1 and selection['State'].iloc[0]!=opd.defs.MULTI and \
        selection['Agency'].nunique()==1 and selection['Agency'].iloc[0]!=opd.defs.MULTI and \
        pd.notnull(selection['AgencyFull'].iloc[0]) and len(selection['AgencyFull'].iloc[0])>0:
        
        test_url = npi_url + 'states/' + selection['State'].iloc[0].replace(' ','-') + '?'

        # Test if state URL exists
        r = requests.get(test_url, timeout=3)
        try:
            r.raise_for_status()
            if 'placeholder="Search Data"' in r.text:
                # There currently is no way to tell if agency URL exists. If it does not, it will go to the state URL and show no results
                test_url += 'agency=' + selection['AgencyFull'].iloc[0].replace(' ','+')
                npi_url = test_url  # URL contains placeholders for data because data exists
        except:
            pass

st.subheader('Other Data Sources')
st.markdown('[OpenPoliceData](https://openpolicedata.readthedocs.io/) recommends these additional police data sources:')
st.markdown(f'**National Police Index** (Police Employment History): '+npi_url)
st.markdown('**Police Data Access Point**: https://pdap.io/')
st.markdown('**Stanford Open Policing Project**: https://openpolicing.stanford.edu/')
st.markdown('**Mapping Police Violence**: https://mappingpoliceviolence.us/')
st.markdown('**Washington Post Fatal Force Database**: https://www.washingtonpost.com/graphics/investigations/police-shootings-database/')
st.markdown('Know of an additional source of data? Please [contact us](mailto:openpolicedata@gmail.com)!')