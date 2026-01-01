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
args, _ = parser.parse_known_args()
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

with st.sidebar:
    st.title('OpenPoliceData Explorer')
    st.caption("Explorer uses the [OpenPoliceData](https://openpolicedata.readthedocs.io/en/stable/documentation.html) Python library to access over 500 "+
            "incident-level datasets from police departments around the United States "+
            "including traffic stops, use of force, and officer-involved shootings data.")

st.session_state['data_catalog'] = get_data_catalog()

page2 = '2_Find_Datasets.py'
pg = st.navigation(["1_Download_Data.py", page2], position='top')

query = st.query_params.to_dict()
if st.session_state['is_starting_up'] and len(query)>0:
    # URL contains query. Set defaults from query.
    if st.context.url is None:
        # App is being tested
        key = 'datasets' if pg.title=='Find Datasets' else 'download'
    else:
        # Deployed app
        key = 'datasets' if st.context.url.endswith(page2[2:].strip('.py')) else 'download'

    logger.info(f'Query: {query}')
    for k,v in query.items():
        if k in st.session_state['default'][key]:
            st.session_state['default'][key][k] = v
        elif k=='table' and 'table_type_general' in st.session_state['default'][key]: # Handle shorthand
            st.session_state['default'][key]['table_type_general'] = v

pg.run()

st.info("Questions or Suggestions? Please reach out to us on our "
            "[discussion board](https://github.com/openpolicedata/openpolicedata/discussions) or by [email](openpolicedata@gmail.com).\n\n"+
            "NOTE: All data is downloaded directly from the source and is not altered in any way. "+
            "Column names and codes may be difficult to understand. Check the data dictionary and "+
            "source URLs for more information. If you still are having issues, feel free to reach out to us at the link above.")

st.session_state['is_starting_up'] = False