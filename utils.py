from io import BytesIO
import math
import openpolicedata as opd
from openpolicedata import data_loaders
import pandas as pd
import streamlit as st
import re
from urllib.parse import urlparse

from streamlit_logger import Code

NA_DISPLAY_VALUE = "NOT APPLICABLE"
ALL = "ALL"

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


def get_default(vals, default_val, required=True):
    if default_val!=0:
        default_val_index = [k for k,x in enumerate(vals) if x==default_val]
        if len(default_val_index)>0:
            default_val_index = default_val_index[0]
        elif required:
            raise ValueError(f"Unable to find requested default {default_val} in {vals}")
        else:
            default_val_index = 0
    else:
        default_val_index = 0

    return default_val_index

def split_tables(table_types):
    isstr = isinstance(table_types, str)
    if isstr:
        table_types = [table_types]

    # Table types that may be split into multiple sub-tables
    split_tables = ["COMPLAINTS", "CRASHES", "OFFICER-INVOLVED SHOOTINGS","USE OF FORCE"]
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

    if isstr:
        table_type_general = table_type_general[0]
        table_type_general_sort = table_type_general_sort[0]
        table_types_sub = table_types_sub[0]

    return table_type_general, table_type_general_sort, table_types_sub


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
                    data_from_url = data_loaders.download_zip_and_extract(selected_rows.iloc[0]["URL"], block_size=2**20, pbar=True)
                    logger.code_reached(Code.FETCH_DATA_STANFORD)
                    nrows = data_loaders.count_csv_rows(data_from_url)
                else:
                    logger.info(f"Loading data for for {selection['year']=}, {selection['table']=}, {selection['agency']=}, "+\
                                    f'{selected_rows.iloc[0]["URL"]=}, {selected_rows.iloc[0]["dataset_id"]=}')
                    data_from_url = src.load(year=selection['year'], table_type=selection['table'], agency=selection['agency'],
                                                url=selected_rows.iloc[0]["URL"], 
                                                id=selected_rows.iloc[0]["dataset_id"],
                                                verbose=False).table
                    logger.code_reached(Code.FETCH_DATA_LOAD_WO_COUNT)
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
            logger.code_reached(Code.FETCH_DATA_LOAD_WITH_COUNT)
        except Exception as e:
            logger.exception('Load failure occurred', exc_info=e)
            load_failure = True
            
        if not load_failure and len(df_list)>0:
            data_from_url = pd.concat(df_list)
        nrows = len(data_from_url)

    if not load_failure and nrows>0:
        nrows_prev = 20
        if is_csv:
            df_prev = pd.read_csv(BytesIO(data_from_url), encoding_errors='surrogateescape', skiprows=0, nrows=nrows_prev)
        else:
            df_prev = data_from_url.head(nrows_prev)
            data_from_url = data_from_url.to_csv(index=False)
            data_from_url = data_from_url.encode('utf-8', 'surrogateescape')

        pd.set_option('future.no_silent_downcasting', True)
        try:
            # Replace non-ASCII characters with '' because st.dataframe will throw an error otherwise
            df_prev = df_prev.replace({r'[^\x00-\x7F]+':''}, regex=True).infer_objects()
            logger.code_reached(Code.PREVIEW_REGEXREP_SUCCESS)
        except:
            pass

        pd.reset_option('future.no_silent_downcasting')
        
    return data_from_url, nrows, df_prev, load_failure

def get_unique_urls(urls, dataset_ids):
    if isinstance(urls, str):
        urls = [urls]
    elif isinstance(urls, pd.Series):
        urls = urls.tolist()

    if isinstance(dataset_ids, str):
        dataset_ids = [dataset_ids]
    elif isinstance(dataset_ids, pd.Series):
        dataset_ids = dataset_ids.tolist()

    unique_urls = []
    for u,d in zip(urls, dataset_ids):
        if urls.count(u)==1 or d is None:
            o = urlparse(u)
            if sum([o.hostname in x for x in urls])<2:
                # hostname is unique
                unique_urls.append(o.hostname)
            else:
                unique_urls.append(u)
        else:
            unique_urls.append(f'{u}: {d}')

    return unique_urls
