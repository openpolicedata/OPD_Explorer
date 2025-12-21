import pandas as pd
import numpy as np
import json

def check_last_selection(app, url, id):
    assert app.session_state['last_selection'][0]==url
    assert (len(app.session_state['last_selection'])==1 and pd.isnull(id)) or \
        app.session_state['last_selection'][1]==id

def get_widget(items, label, required=True):
    result = [x for x in items if x.label==label]
    assert not required or len(result)!=0, f'No results found for label {label}'
    assert len(result)<2, f'Multiple results found for label {label}'

    return result[0] if len(result)>0 else None


def get_state_filter(app):
    return get_widget(app.sidebar.selectbox, 'States')

def get_source_filter(app):
    return get_widget(app.sidebar.selectbox, 'Sources')

def get_table_filter(app):
    return get_widget(app.sidebar.selectbox, 'Table Types')

def get_year_filter(app):
    return get_widget(app.sidebar.selectbox, 'Years')

def match_dataframes(df_true, df_app):
    if 'dataset_id' in df_app:
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
