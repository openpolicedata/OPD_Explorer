import pytest
import openpolicedata as opd
import pandas as pd
import numpy as np
import json

import utils
import url
from .test_fcns import *

@pytest.fixture(autouse=True)  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def ensure_correct_page(app):
    app.switch_page("2_Find_Datasets.py").run()
    get_state_filter(app).select(utils.ALL).run()
    get_source_filter(app).select(utils.ALL).run()
    get_table_filter(app).select(utils.ALL).run()

    yield
    # Ensure that values set for query are reset
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.run()


def match_dataframes(df_true, df_app):
    df_app['dataset_id'] = df_app['dataset_id'].apply(lambda x: np.nan if x=='nan' else x)
    
    df_app = df_app.convert_dtypes()
    df_true = df_true.convert_dtypes()

    for c in df_true.columns:
        if df_true[c].dtype != df_app[c].dtype:
            df_app[c] = df_app[c].astype(df_true[c].dtype)
        if df_true[c].dtype=='object':
            # Ensure each value has same type
            app_vals = df_app[c].tolist()
            true_vals = df_true[c].tolist()
            for k in range(len(true_vals)):
                if type(true_vals[k]) != type(app_vals[k]):
                    # Convert to same type
                    if pd.isnull(app_vals[k]) and pd.isnull(true_vals[k]):
                        app_vals[k] = true_vals[k]
                    elif isinstance(true_vals[k], dict) and isinstance(app_vals[k], str):
                        app_vals[k] = json.loads(app_vals[k].replace("'",'"'))
                    else:
                        app_vals[k] = type(true_vals[k])(app_vals[k])

            df_app[c] = app_vals
            df_app[c] = df_app[c].astype(df_true[c].dtype)

        if df_true[c].dtype != df_app[c].dtype:
            df_app[c] = df_app[c].astype(df_true[c].dtype)

    return df_true, df_app

@pytest.mark.parametrize('state, src, table', [
    ('North Dakota', None, None),
    ('Colorado', 'Denver', None),
    ('California', None, 'STOPS'),
    ('California', 'Los Angeles', 'STOPS'),
    (None, 'State Police', None),
    (None, 'State Patrol', 'TRAFFIC STOPS'),
    (None, None, 'OFFICER-INVOLVED SHOOTINGS')
])
@pytest.mark.parametrize('from_url',[False, True])
def test_filter(app, state, src, table, from_url):

    if from_url:
        # We currently cannot set the URL for the test so simulate receipt of a URL
        query_url = url.get_opd_explorer_dataset_url(state, src, table, url_type='local')
        idx = query_url.find('?')
        queries = query_url[idx+1:].split('&')
        app.query_params = {}
        for q in queries:
            k,v = q.split('=')
            app.query_params[k]=v

        app.session_state['is_starting_up'] = True # Trigger re-initializing since we can't reload the page in testing
        app.run()
    else:
        if state:
            get_state_filter(app).select(state).run()

        if src:
            get_source_filter(app).select(src).run()

        if table:
            get_table_filter(app).select(table).run()

    assert get_state_filter(app).value==state if state else utils.ALL
    assert get_source_filter(app).value==src if src else utils.ALL
    assert get_table_filter(app).value==table if table else utils.ALL
    
    df_true = opd.datasets.query(state=state, source_name=src)
    if table:
        df_true = df_true[df_true['TableType'].str.startswith(table)]

    assert len(df_true)>0
    df_true, df_app = match_dataframes(df_true, app.dataframe[0].value)

    pd.testing.assert_frame_equal(df_true[['URL','dataset_id']], df_app[['URL','dataset_id']])