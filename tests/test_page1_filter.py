import pytest
import openpolicedata as opd
import pandas as pd

from .test_fcns import *
import utils

@pytest.fixture(autouse=True)  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def ensure_correct_page(app):
    app.switch_page("1_Download_Data.py").run()
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.run()

    yield
    # Ensure that values set for query are reset
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.run()


def test_basic_multiyear_file(app):
    state = 'Colorado'
    src = 'Denver'
    tbl = 'OFFICER-INVOLVED SHOOTINGS'
    url = 'https://raw.githubusercontent.com/openpolicedata/opd-datasets/main/data/Colorado_Denver_OFFICER-INVOLVED_SHOOTINGS.csv'
    id = pd.NA

    df = opd.datasets.query(state=state, source_name=src, table_type=tbl)
    assert len(df)==1, 'This test case is no longer a basic case'
    assert df.iloc[0]['Year']==opd.defs.MULTI, 'This test case is no longer multiyear'
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl

    year = f"{df.iloc[0]['coverage_start'].year}-{df.iloc[0]['coverage_end'].year}"
    assert get_year_filter(app).value==year

    check_last_selection(app, url, id)


def test_basic_singleyear(app):
    state = 'District of Columbia'
    src = 'Washington D.C.'
    tbl = 'USE OF FORCE'
    year = '2022'
    url = 'https://mpdc.dc.gov/sites/default/files/dc/sites/mpdc/publication/attachments/external%20use%20of%20force%20full%20year%202022%202023-12-04.xlsx'
    id = pd.NA
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    get_year_filter(app).select(year).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl
    assert get_year_filter(app).value==year

    check_last_selection(app, url, id)


def test_multiple_urls_match(app):
    state = 'North Carolina'
    src = 'Asheville'
    tbl = 'USE OF FORCE'
    year = '2020'
    url = 'https://services.arcgis.com/aJ16ENn1AaqdFlqx/arcgis/rest/services/APD_UseOfForce2021/FeatureServer/0'
    id = pd.NA
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    get_year_filter(app).select(year).run()
    get_widget(app.sidebar.selectbox, 'Multiple Options: Select URL+ID').select(url).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl
    assert get_year_filter(app).value==year
    assert get_widget(app.sidebar.selectbox, 'Multiple Options: Select URL+ID').value==url

    check_last_selection(app, url, id)

def test_subtable_and_NA_year(app):
    state = 'North Carolina'
    src = 'Asheville'
    tbl = 'TRAFFIC STOPS'
    subtable = 'SUBJECTS'
    year = utils.NA_DISPLAY_VALUE
    url = 'https://services.arcgis.com/aJ16ENn1AaqdFlqx/arcgis/rest/services/APDTrafficStopTables/FeatureServer/1'
    id = pd.NA
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    get_widget(app.sidebar.selectbox, 'Table Subcategory').select(subtable).run()
    get_year_filter(app).select(year).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl
    assert get_year_filter(app).value==year
    assert get_widget(app.sidebar.selectbox, 'Table Subcategory').value==subtable

    for m in app.markdown:
        if 'Related tables' in m.value:
            break
    else:
        raise ValueError('Unable to find related table text')

    check_last_selection(app, url, id)


def test_multiple_agencies_for_source(app):
    state = 'California'
    src = 'Contra Costa County'
    tbl = 'STOPS'
    agency = 'MULTIPLE'
    year = '2022'
    url = 'https://data-openjustice.doj.ca.gov/sites/default/files/dataset/2023-12/RIPA-Stop-Data-2022.zip'
    id = 'RIPA Stop Data _ Contra Costa 2022.xlsx'
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    get_widget(app.sidebar.selectbox, 'Agencies').select(agency).run()
    get_year_filter(app).select(year).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl
    assert get_year_filter(app).value==year
    assert get_widget(app.sidebar.selectbox, 'Agencies').value==agency

    check_last_selection(app, url, id)
    

def test_source_contains_multiple_agencies(app):
    state = 'Virginia'
    src = 'Virginia'
    tbl = 'STOPS'
    agency = 'Abingdon Police Department'
    year = '2020'
    url = 'https://data.virginia.gov'
    id = '60506bbb-685f-4360-8a8c-30e137ce3615'
    
    # Must re-get selectboxes each time because they are recreated every time run is called
    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(tbl).run()
    get_year_filter(app).select(year).run()
    get_widget(app.sidebar.selectbox, 'Agencies').select(agency).run()

    assert get_state_filter(app).value==state
    assert get_source_filter(app).value==src
    assert get_table_filter(app).value==tbl
    assert get_year_filter(app).value==year
    assert get_widget(app.sidebar.selectbox, 'Agencies').value==agency

    check_last_selection(app, url, id)