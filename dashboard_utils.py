from io import BytesIO
import math
import openpolicedata as opd
from openpolicedata import data_loaders
import pandas as pd
import streamlit as st
import utils

@st.cache_data(show_spinner="Loading year information...")
def get_years(selectbox_sources, selectbox_states, selectbox_table_types, selected_agency):
    src = opd.Source(selectbox_sources, state=selectbox_states, agency=selected_agency)
    years = src.get_years(table_type=selectbox_table_types, force=False)
    years.sort(reverse=True)
    return [str(x) if x!=opd.defs.NA else utils.NA_DISPLAY_VALUE for x in years]


@st.cache_data(show_spinner="Loading agency information...")
def get_agencies(selectbox_sources, selectbox_states, selectbox_table_types, year, selected_agency,
                 url_contains, id_contains):
    src = opd.Source(selectbox_sources, state=selectbox_states, agency=selected_agency)
    agencies = src.get_agencies(table_type=selectbox_table_types, year=year, url=url_contains, id=id_contains)
    agencies.sort()
    agencies.insert(0, utils.ALL)
    return agencies


def load(src, selection, selected_rows, record_count, msgs):
    logger = st.session_state['logger']

    data_from_url = []
    df_prev = []
    load_failure = False
    is_csv = False
    nrows = -1

    logger.info(f"Loading data for for {selection['year']=}, {selection['table']=}, {selection['agency']=}, "+\
                                    f'{selected_rows.iloc[0]["URL"]=}, {selected_rows.iloc[0]["dataset_id"]=}')

    if record_count is None:
        with st.spinner(msgs['wait']):
            try:
                if 'stacks.stanford.edu' in selected_rows.iloc[0]["URL"]:
                    # For large datasets on Streamlit cloud, OPD Explorer fails when converting the entire file to a DataFrame
                    # Instead, just download data and only convert enough rows to a DataFrame to create the preview
                    is_csv = True
                    data_from_url = data_loaders.data_loader.download_zip_and_extract(selected_rows.iloc[0]["URL"], block_size=2**20, pbar=True)
                    nrows = data_loaders.csv_class.count_csv_rows(data_from_url)
                else:
                    logger.info(f"Loading data for for {selection['year']=}, {selection['table']=}, {selection['agency']=}, "+\
                                    f'{selected_rows.iloc[0]["URL"]=}, {selected_rows.iloc[0]["dataset_id"]=}')
                    data_from_url = src.load(year=selection['year'], table_type=selection['table'], agency=selection['agency'],
                                                url=selected_rows.iloc[0]["URL"], 
                                                id=selected_rows.iloc[0]["dataset_id"],
                                                verbose=False).table
                    nrows = len(data_from_url)
            except Exception as e:
                logger.exception('Load failure occurred', exc_info=e)
                load_failure = True
    else:
        df_list = []
        batch_size = 5000
        nbatches = math.ceil(record_count / batch_size)
        pbar = st.progress(0, text=msgs['wait'])
        iter = 0
        try:
            for tbl in src.load_iter(year=selection['year'], table_type=selection['table'], nbatch=batch_size, agency=selection['agency'],
                                        url_contains=selected_rows.iloc[0]["URL"], 
                                        id_contains=selected_rows.iloc[0]["dataset_id"]):
                iter+=1
                df_list.append(tbl.table)
                pbar.progress(iter / nbatches, text=msgs['wait'])
        except Exception as e:
            logger.exception('Load failure occurred', exc_info=e)
            load_failure = True
            
        if not load_failure and len(df_list)>0:
            data_from_url = pd.concat(df_list)
        nrows = len(data_from_url)

    if not load_failure and nrows>0:
        if is_csv:
            df_prev = pd.read_csv(BytesIO(data_from_url), encoding_errors='surrogateescape', skiprows=0, nrows=utils.NROWS_PREVIEW)
        else:
            df_prev = data_from_url.head(utils.NROWS_PREVIEW)
            data_from_url = data_from_url.to_csv(index=False)
            data_from_url = data_from_url.encode('utf-8', 'surrogateescape')

        pd.set_option('future.no_silent_downcasting', True)
        try:
            # Replace non-ASCII characters with '' because st.dataframe will throw an error otherwise
            df_prev = df_prev.replace({r'[^\x00-\x7F]+':''}, regex=True).infer_objects()
        except:
            pass

        pd.reset_option('future.no_silent_downcasting')
        
    return data_from_url, nrows, df_prev, load_failure


def get_default(name, vals, default_val):
    if isinstance(default_val, dict):
        default_val = default_val[name]

    default = utils.get_default(vals, default_val, required=False)

    if default==None:
        st.toast(f"ERROR: Requested {name}={default_val} not found", duration='infinite', icon=":material/error:")
        default = 0

    return default

def set_defaults_to_go_to_dataset(selected_ds):
    st.session_state['default']['download']['state'] = selected_ds['State']
    st.session_state['default']['download']['source'] = selected_ds['SourceName']
    st.session_state['default']['download']['table_type_general'], _, st.session_state['default']['download']['table_type_sub'] = utils.split_tables(selected_ds['TableType'])
    st.session_state['default']['download']['agency'] = selected_ds['Agency']
    years = get_years(selected_ds['SourceName'], selected_ds['State'], selected_ds['TableType'], selected_ds['Agency'])
    st.session_state['default']['download']['year'] = years[0]
    st.session_state['default']['download']['url'] = selected_ds['URL']
    st.session_state['default']['download']['id'] = selected_ds['dataset_id']