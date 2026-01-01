import warnings

from .test_fcns import *

def test_go_to_dataset(app):
    state = 'North Carolina'
    src = 'Charlotte-Mecklenburg'
    table = 'OFFICER-INVOLVED SHOOTINGS'

    app.switch_page('2_Find_Datasets.py').run()

    get_state_filter(app).select(state).run()
    get_source_filter(app).select(src).run()
    get_table_filter(app).select(table).run()

    warnings.warn('test_go_to_dataset: It does not appear to currently be possible to select a row. Therefore, pytest cannot test going to a dataset. This must be tested manually')