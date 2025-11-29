import pytest
from streamlit.testing.v1 import AppTest

@pytest.fixture(scope='session')
def app(request):
    at = AppTest.from_file('opd_download_page.py', default_timeout=60)
    at.run()
    assert not at.exception

    return at