from datetime import datetime, timezone
import streamlit as st
from streamlit_logger import create_logger
import openpolicedata as opd

@st.cache_data()
def display_version(opd_version, exp_version, st_version):
    now = datetime.now(timezone.utc)

    st.session_state['logger'].info(now)
    st.session_state['logger'].info("VERSIONS:")
    st.session_state['logger'].info(f"\tOpenPoliceData: {opd_version}")
    st.session_state['logger'].info(f"\tOPD Explorer: {exp_version}")
    st.session_state['logger'].info(f"\tStreamlit: {st_version}")  # 4/28/2025: Working ver =  1.44.1
    st.session_state['logger'].info(f'URL: {st.context.url}')
    st.session_state['logger'].info(f'IP: {st.context.ip_address}')
    st.session_state['logger'].info(f'Locale: {st.context.locale}')
    st.session_state['logger'].info(f'User Timezone: {st.context.timezone}')
    st.session_state['logger'].info(f'User Timezone Offset: {st.context.timezone_offset}')


def init(level, __version__):
    if 'is_starting_up' not in st.session_state or st.session_state['is_starting_up']:  # st.session_state['is_starting_up']=True is only needed for testing
        st.session_state['logger'] = create_logger(name = 'opd-app', level = level)
        st.session_state['last_selection'] = None
        st.session_state['is_starting_up'] = True  # Indicates that the app has just been instantiated
        st.session_state['preview'] = None

        # Key order is important. It is used for reseting defaults properly. See clear_defaults.
        st.session_state['default'] = {
            'download':{k:0 for k in ['state','source','table_type_general','table_type_sub','agency','year', 'url']},
            'datasets':{k:0 for k in ['state','source','table']}
        }

        st.session_state['logger'].debug("***********DEBUG MODE*************")

        display_version(opd.__version__, __version__, st.__version__)


def clear_defaults(page, start):
    # Clearing defaults results in changing of value
    # Can safely clear dependent defaults (i.e. defaults below changed parameter) of changed parameter
    skip = True
    for k in st.session_state['default'][page].keys():
        if skip:
            skip = k!=start  # Reset everything after this
        else:
            st.session_state['default'][page][k]=0
    
