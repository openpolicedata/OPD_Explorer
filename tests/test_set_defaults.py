import pytest
import pandas as pd
import numpy as np
from copy import deepcopy
from urllib.parse import urlparse
import openpolicedata as opd

from .test_fcns import *

@pytest.fixture()  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def app_page1(app):
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.switch_page("1_Download_Data.py").run()

    yield app
    # Ensure that values set for query are reset
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.run()


@pytest.fixture()  # Setup function to ensure that each test is on correct page. autouse means it will be created despite not being passed into the tests
def app_page2(app):
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.switch_page("2_Find_Datasets.py").run()

    yield app
    # Ensure that values set for query are reset
    app.session_state['is_starting_up'] = True
    app.query_params = {}
    app.run()


def test_page1_subtable(app_page1):
    app = app_page1

    d = app.session_state['default']['download']
    d['state'] = 'North Carolina'
    d['source'] = 'Asheville'
    d['table_type_general'] = 'TRAFFIC STOPS'
    d['table_type_sub'] = 'SUBJECTS'

    app.run()

    url = 'https://services.arcgis.com/aJ16ENn1AaqdFlqx/arcgis/rest/services/APDTrafficStopTables/FeatureServer/1'
    id = np.nan

    assert get_state_filter(app).value==d['state']
    assert get_source_filter(app).value==d['source']
    assert get_table_filter(app).value==d['table_type_general']
    assert get_widget(app.sidebar.selectbox, 'Table Subcategory').value==d['table_type_sub']

    check_last_selection(app, url, id)
    
    # Change the filter values to trigger resets
    app.session_state['default']['download'] = deepcopy(d)
    get_widget(app.sidebar.selectbox, 'Table Subcategory').select('INCIDENTS').run()
    assert app.session_state['default']['download']['table_type_sub'] == d['table_type_sub']

    app.session_state['default']['download'] = deepcopy(d)
    get_table_filter(app).select('CALLS FOR SERVICE').run()
    assert app.session_state['default']['download']['table_type_sub'] == 0
    assert app.session_state['default']['download']['table_type_general'] == d['table_type_general']

    app.session_state['default']['download'] = deepcopy(d)
    get_state_filter(app).select('Arizona').run()
    assert app.session_state['default']['download']['table_type_sub'] == 0
    assert app.session_state['default']['download']['table_type_general'] == 0
    assert app.session_state['default']['download']['source'] == 0
    assert app.session_state['default']['download']['state'] == d['state']


def set_to_different_option(widget):
    for o in widget.options:
        if o!=widget.value:
            widget.select(o).run()
            break


@pytest.mark.parametrize('state, source , table, year, id, url', [
    ('North Carolina', 'Asheville', 'USE OF FORCE', 2020, np.nan, 
        'https://services.arcgis.com/aJ16ENn1AaqdFlqx/arcgis/rest/services/APD_UseOfForce2021/FeatureServer/0'),
    ('Colorado', 'Colorado Springs', 'ARRESTS', 2020, '34jw-x9zp', 'policedata.coloradosprings.gov'),
    ('North Carolina', 'Charlotte-Mecklenburg', 'TRAFFIC STOPS', 2015, np.nan, 'https://gis.charlottenc.gov/arcgis/rest/services/CMPD/Officer_Traffic_Stop/MapServer/0')
])
def test_page1_multiple_urls(app_page1, state, source, table, year, id, url):
    app = app_page1

    d = app.session_state['default']['download']
    d['state'] = state
    d['source'] = source
    d['table_type_general'] = table
    d['year'] = str(year)
    d['url'] = url
    d['id'] = id

    app.run()

    assert get_state_filter(app).value==d['state']
    assert get_source_filter(app).value==d['source']
    assert get_table_filter(app).value==d['table_type_general']
    assert get_year_filter(app).value==d['year']

    # Get URL/ID code. Note this logic may not work in all possible cases that could be tested!
    df = opd.datasets.query()
    df =df[(df['State']==d['state']) & (df['SourceName']==d['source']) & (df['TableType']==d['table_type_general'])]
    all_urls = df['URL'].tolist()
    if all(x==all_urls[0] for x in all_urls):
        url_id = f'{url}: {id}'
    elif all(urlparse(x).hostname==urlparse(all_urls[0]).hostname for x in all_urls):
        url_id = url
    else:
        url_id = urlparse(url).hostname

    assert get_widget(app.sidebar.selectbox, 'Multiple Options: Select URL+ID').value==url_id

    check_last_selection(app, url, id)
    
    # Change the filter values to trigger resets
    app.session_state['default']['download'] = deepcopy(d)
    set_to_different_option(get_widget(app.sidebar.selectbox, 'Multiple Options: Select URL+ID'))
    assert app.session_state['default']['download']['url'] == d['url']

    app.session_state['default']['download'] = deepcopy(d)
    set_to_different_option(get_year_filter(app))
    assert app.session_state['default']['download']['url'] == 0
    assert app.session_state['default']['download']['year'] == d['year']

    app.session_state['default']['download'] = deepcopy(d)
    set_to_different_option(get_table_filter(app))
    assert app.session_state['default']['download']['url'] == 0
    assert app.session_state['default']['download']['year'] == 0
    assert app.session_state['default']['download']['table_type_general'] == d['table_type_general']

    app.session_state['default']['download'] = deepcopy(d)
    set_to_different_option(get_state_filter(app))
    assert app.session_state['default']['download']['url'] == 0
    assert app.session_state['default']['download']['year'] == 0
    assert app.session_state['default']['download']['table_type_general'] == 0
    assert app.session_state['default']['download']['source'] == 0
    assert app.session_state['default']['download']['state'] == d['state']


def test_page1_multiple_agencies(app_page1):
    app = app_page1

    d = app.session_state['default']['download']
    d['state'] = 'California'
    d['source'] = 'Contra Costa County'
    d['table_type_general'] = 'STOPS'
    d['agency'] = 'MULTIPLE'
    d['year'] = '2022'

    app.run()
    
    url = 'https://data-openjustice.doj.ca.gov/sites/default/files/dataset/2023-12/RIPA-Stop-Data-2022.zip'
    id = 'RIPA Stop Data _ Contra Costa 2022.xlsx'

    assert get_state_filter(app).value==d['state']
    assert get_source_filter(app).value==d['source']
    assert get_table_filter(app).value==d['table_type_general']
    assert get_widget(app.sidebar.selectbox, 'Agencies').value==d['agency']
    assert get_year_filter(app).value==d['year']

    check_last_selection(app, url, id)
    
    # Change the filter values from top to bottom to trigger resets
    app.session_state['default']['download'] = deepcopy(d)
    get_year_filter(app).select('2023').run()
    assert app.session_state['default']['download']['year'] == d['year']

    app.session_state['default']['download'] = deepcopy(d)
    get_widget(app.sidebar.selectbox, 'Agencies').select('Contra Costa County').run()
    assert app.session_state['default']['download']['year'] == 0
    assert app.session_state['default']['download']['agency'] == d['agency']

    app.session_state['default']['download'] = deepcopy(d)
    get_source_filter(app).select('California').run()
    assert app.session_state['default']['download']['year'] == 0
    assert app.session_state['default']['download']['agency'] == 0
    assert app.session_state['default']['download']['table_type_general'] == 0
    assert app.session_state['default']['download']['source'] == d['source']

    app.session_state['default']['download'] = deepcopy(d)
    get_state_filter(app).select('Arizona').run()
    assert app.session_state['default']['download']['year'] == 0
    assert app.session_state['default']['download']['agency'] == 0
    assert app.session_state['default']['download']['table_type_general'] == 0
    assert app.session_state['default']['download']['source'] == 0
    assert app.session_state['default']['download']['state'] == d['state']


def test_page2(app_page2):
    app = app_page2

    d = app.session_state['default']['datasets']
    d['state'] = 'North Carolina'
    d['source'] = 'Charlotte-Mecklenburg'
    d['table'] = 'OFFICER-INVOLVED SHOOTINGS'

    app.run()

    assert get_state_filter(app).value==d['state']
    assert get_source_filter(app).value==d['source']
    assert get_table_filter(app).value==d['table']
    
    # Change the filter values from top to bottom to trigger resets
    app.session_state['default']['datasets'] = deepcopy(d)
    assert app.session_state['default']['datasets']['table'] == d['table']

    app.session_state['default']['datasets'] = deepcopy(d)
    get_source_filter(app).select('Asheville').run()
    assert app.session_state['default']['datasets']['table'] == 0
    assert app.session_state['default']['datasets']['source'] == d['source']

    app.session_state['default']['datasets'] = deepcopy(d)
    get_state_filter(app).select('Arizona').run()
    assert app.session_state['default']['datasets']['table'] == 0
    assert app.session_state['default']['datasets']['source'] == 0
    assert app.session_state['default']['datasets']['state'] == d['state']


def test_bad_default_value(app):
    pages = ["1_Download_Data.py", '2_Find_Datasets.py']
    fake_val = 'FAKE'
    key = 'state'
    for p in app.session_state['default'].keys():
        curpage = [x for x in pages if p.lower() in x.lower()]
        
        app.session_state['default'][p][key] = fake_val
        app.switch_page(curpage[0]).run()

        # Ensure that warning message is displayed
        assert len(app.toast)>0
        assert fake_val in app.toast[0].value
        assert key in app.toast[0].value
