import pytest
import openpolicedata as opd
from io import BytesIO
import pandas as pd

from .test_fcns import *
import utils

@pytest.fixture(autouse=True)  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def ensure_correct_page(app):
    app.switch_page("1_Download_Data.py").run()

def match_dataframes(df_true, df_app):
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
                    app_vals[k] = type(true_vals[k])(app_vals[k])

            df_app[c] = app_vals
            df_app[c] = df_app[c].astype(df_true[c].dtype)

    return df_app

@pytest.mark.parametrize("state, src, tbl, year, id, url",
                         [('California', 'Stockton', 'OFFICER-INVOLVED SHOOTINGS', 'MULTIPLE', pd.NA, 'https://cdn.muckrock.com/foia_files/2022/02/15/Sinyangwe_Samuel_-_20220115_-_CPRA_Information.xlsx'),
                          ('California', 'Richmond', 'OFFICER-INVOLVED SHOOTINGS', '2015', 'asfd-zcvn', 'www.transparentrichmond.org'),
                          ('Kentucky', 'Owensboro', 'STOPS', 'MULTIPLE', pd.NA, 'https://stacks.stanford.edu/file/druid:yg821jf8611/yg821jf8611_ky_owensboro_2020_04_01.csv.zip')
                          ])
def test_preview(app, state, src, tbl, year, id, url, reset=True):
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    if year!="MULTIPLE":
        get_year_filter(app).select(year).run()

    assert app.session_state['last_selection'][0]==url
    assert (pd.isnull(app.session_state['last_selection'][1]) and pd.isnull(id)) or \
        app.session_state['last_selection'][1]==id

    # Download storage variables should start empty
    assert len(app.session_state['preview'])==0
    assert app.session_state['csv_text_output']==None

    nrows = 10
    get_widget(app.number_input,'Number of Rows').set_value(nrows).run()

    assert get_widget(app.number_input,'Number of Rows').value==nrows

    get_widget(app.button,'Preview').click().run()

    ds = opd.datasets.query(state=state, source_name=src, table_type=tbl)

    assert len(ds)==1
    ds = ds.iloc[0]

    if ds['DataType'] in utils.API_DATA_TYPES or (ds['DataType']=='CSV' and not ds['URL'].endswith('zip')):
        assert app.session_state['csv_text_output']==None
    else:
        assert app.session_state['csv_text_output']!=None

    s = opd.Source(src, state=state)
    t = s.load(tbl, int(year) if year.isdigit() else year)

    assert len(app.session_state['preview']) == min(nrows, len(t.table))
    df_preview = t.table.iloc[:len(app.session_state['preview'])]

    df2 = match_dataframes(df_preview, app.session_state['preview'])

    pd.testing.assert_frame_equal(df_preview, df2)

    # df_app = pd.read_csv(BytesIO(app.session_state['csv_text_output']))

    # assert len(t.table)==len(df_app)
    # assert (t.table.columns==df_app.columns).all()

    # df_app = match_dataframes(t.table, df_app)
    # pd.testing.assert_frame_equal(df_app, t.table)

    # assert get_widget(app.button,'Retrieve Data', required=False) is None # This button should not exist

    # Cannot test data downloading. It appears that there is no download button available

    if reset:
        # Ensure that filter change causes reset 
        get_state_filter(app).select('Texas').run()
        assert len(app.session_state['preview'])==0
        assert app.session_state['csv_text_output']==None

