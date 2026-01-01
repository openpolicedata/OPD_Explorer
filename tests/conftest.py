import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

@pytest.fixture(scope='session')
def app(request):
    at = AppTest.from_file('opd_download_page.py', default_timeout=60)
    at.run()
    assert not at.exception

    return at

# Create testable download_button
class DownloadButton(object): # Singleton class (only be created once)
    def __new__(cls, label=None, data=None, file_name=None, mime=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DownloadButton, cls).__new__(cls)
            cls.instance.value = False

        cls.instance.label = label
        cls.instance.data = data
        cls.instance.file_name = file_name
        cls.instance.mime = mime

        return cls.instance
    
    def click(self):
        self.value = True
  

def download_button(label, data, file_name, mime):
    btn = DownloadButton(label, data, file_name, mime)

    out = btn.value
    if out and callable(btn.data):
        btn.data = data()
    # Set to False to revert value after a button click
    btn.value = False
    return out

def columns(ncols, *args, **kwargs):
    all_cols = st._main.columns(ncols, *args, **kwargs)
    for c in all_cols:
        c.download_button = download_button

    return all_cols

st.download_button = download_button
st.columns = columns