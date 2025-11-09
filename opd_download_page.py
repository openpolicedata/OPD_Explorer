import streamlit as st
import argparse
import logging
from packaging import version
import pandas as pd

import init
import openpolicedata as opd

__version__ = "2.0"

st.set_page_config(
    page_title="OpenPoliceData",
    page_icon="🌃",
    layout='wide',
    initial_sidebar_state="expanded",
    menu_items={
        'Report a Bug': "https://github.com/openpolicedata/OPD_Explorer/issues"
    }
)

# Must add -- before arguments so that streamlit does not try to read our args
# i.e. -- --debug
# https://discuss.streamlit.io/t/command-line-arguments/386/4
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true')
args = parser.parse_args()
level = logging.DEBUG if args.debug else logging.INFO

init.init(level, __version__)

logger = st.session_state['logger']
    
@st.cache_data(show_spinner="Updating datasets...", ttl='1 day')
def get_data_catalog():
    print('Getting data catalog')
    if not st.session_state['is_starting_up']:  # Otherwise, the datasets have just been loaded
        opd.datasets.reload()
        print('Reloading data catalog')

    df = opd.datasets.query()
    # Remove min_version = -1 (not available in any version) or min_version > current version
    df = df[df["min_version"].apply(lambda x: 
                                    pd.isnull(x) or (x.strip()!="-1" and version.parse(opd.__version__) >= version.parse(x))
                                    )]
    df = df.sort_values(by=["State","SourceName","TableType"])
    return df

st.title('OpenPoliceData Explorer')
st.caption("Explorer uses the [OpenPoliceData](https://openpolicedata.readthedocs.io/en/stable/documentation.html) Python library to access over 500 "+
           "incident-level datasets from police departments around the United States "+
           "including traffic stops, use of force, and officer-involved shootings data.")

st.session_state['data_catalog'] = get_data_catalog()

pg = st.navigation(["1_Download_Data.py", '2_Find_Datasets.py'], position='top')
pg.run()