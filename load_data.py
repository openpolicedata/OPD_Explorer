from io import BytesIO
import math
from openpolicedata import data_loaders
import pandas as pd
import streamlit as st

from streamlit_logger import Code

def load(src, selection, selected_rows, record_count, msgs):
    logger = st.session_state['logger']

    data_from_url = []
    df_prev = []
    load_failure = False
    is_csv = False

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
                    data_from_url = src.load(year=selection['year'], table_type=selection['table'], agency=selection['agency'],
                                                url_contains=selected_rows.iloc[0]["URL"], 
                                                id_contains=selected_rows.iloc[0]["dataset_id"],
                                                verbose=False).table
                    logger.code_reached(Code.FETCH_DATA_LOAD_WO_COUNT)
                    nrows = len(data_from_url)
            except Exception as e:
                logger.exception('Load failure occurred')
                logger.exception(str(e))
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
        except:
            logger.exception('Load failure occurred')
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