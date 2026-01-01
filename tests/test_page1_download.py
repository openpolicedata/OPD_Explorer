import pytest
import openpolicedata as opd
from io import BytesIO
import pandas as pd

from .test_fcns import *
from .conftest import DownloadButton
import utils

SAVED_CSV = 'csv_text_output'

@pytest.fixture(autouse=True)
def check_download_button_still_not_added_to_streamlit_tests(app):
    # Currently dummy variable created in conftest to handle this download_button testing
    # which can be removed if download_button is added to streamlit testing

    try:
        app.download_button
        raise ValueError("Switch to using app.download_button instead")
    except AttributeError as e:
        pass
    except:
        raise ValueError("Switch to using app.download_button instead")

@pytest.fixture(autouse=True)  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def ensure_correct_page(app):
    app.switch_page("1_Download_Data.py").run()


def test_download_after_preview_load(app):
    app.session_state[SAVED_CSV] = 'TEST'

    btn = DownloadButton()
    btn.click()
    app.run()

    assert btn.data == app.session_state[SAVED_CSV]

    get_state_filter(app).select('Texas').run()
    assert app.session_state[SAVED_CSV] == None
    assert callable(btn.data)


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

    check_last_selection(app, url, id)

    # Download storage variables should start empty
    assert len(app.session_state['preview'])==0
    assert app.session_state[SAVED_CSV]==None

    nrows = 10
    get_widget(app.number_input,'Preview Rows').set_value(nrows).run()

    assert get_widget(app.number_input,'Preview Rows').value==nrows

    get_widget(app.button,'Preview').click().run()

    ds = opd.datasets.query(state=state, source_name=src, table_type=tbl)

    assert len(ds)==1
    ds = ds.iloc[0]

    load_all = not (ds['DataType'] in utils.API_DATA_TYPES or (ds['DataType']=='CSV' and not ds['URL'].endswith('zip')))
    if not load_all:
        assert app.session_state[SAVED_CSV]==None
    else:
        assert app.session_state[SAVED_CSV]!=None

    s = opd.Source(src, state=state)
    t = s.load(tbl, int(year) if year.isdigit() else year)

    assert len(app.session_state['preview']) == min(nrows, len(t.table))
    df_preview = t.table.iloc[:len(app.session_state['preview'])]

    df_preview, df2 = match_dataframes(df_preview, app.dataframe.values[0])
    pd.testing.assert_frame_equal(df_preview, df2)

    # This should not produce a filter change and preview should remain available
    if year!="MULTIPLE":
        get_year_filter(app).select(year).run()
    else:
        get_table_filter(app).select(tbl).run()
    
    df_preview, df2 = match_dataframes(df_preview, app.dataframe.values[0])
    pd.testing.assert_frame_equal(df_preview, df2)

    if load_all:
        df_app = pd.read_csv(BytesIO(app.session_state[SAVED_CSV]))

        assert len(t.table)==len(df_app)
        assert (t.table.columns==df_app.columns).all()

        df, df_app = match_dataframes(t.table, df_app)
        pd.testing.assert_frame_equal(df_app, df)

    if reset:
        # Ensure that filter change causes reset 
        get_state_filter(app).select('Texas').run()
        assert len(app.session_state['preview'])==0
        assert app.session_state[SAVED_CSV]==None

@pytest.mark.parametrize("state, src, tbl, year, id, url",
                         [('California', 'Stockton', 'OFFICER-INVOLVED SHOOTINGS', 'MULTIPLE', pd.NA, 'https://cdn.muckrock.com/foia_files/2022/02/15/Sinyangwe_Samuel_-_20220115_-_CPRA_Information.xlsx'),
                          ('California', 'Richmond', 'OFFICER-INVOLVED SHOOTINGS', '2015', 'asfd-zcvn', 'www.transparentrichmond.org'),
                          ('Kentucky', 'Owensboro', 'STOPS', 'MULTIPLE', pd.NA, 'https://stacks.stanford.edu/file/druid:yg821jf8611/yg821jf8611_ky_owensboro_2020_04_01.csv.zip')
                          ])
def test_download(app, state, src, tbl, year, id, url, reset=True):    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    if year!="MULTIPLE":
        get_year_filter(app).select(year).run()

    check_last_selection(app, url, id)

    # Check that there hasn't been a preview
    assert len(app.session_state['preview'])==0
    assert app.session_state[SAVED_CSV]==None

    btn = DownloadButton()
    btn.click()
    app.run()

    assert isinstance(btn.data, bytes)

    download = btn.data

    ds = opd.datasets.query(state=state, source_name=src, table_type=tbl)

    assert len(ds)==1
    ds = ds.iloc[0]

    s = opd.Source(src, state=state)
    t = s.load(tbl, int(year) if year.isdigit() else year)

    df_app = pd.read_csv(BytesIO(download))

    assert len(t.table)==len(df_app)
    assert (t.table.columns==df_app.columns).all()

    df, df_app = match_dataframes(t.table, df_app)
    pd.testing.assert_frame_equal(df_app, df)

