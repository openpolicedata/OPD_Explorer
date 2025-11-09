from datetime import datetime
import streamlit as st
from streamlit_logger import create_logger
import openpolicedata as opd

@st.cache_data()
def display_version(opd_version, exp_version, st_version):
    now = datetime.now()

    st.session_state['logger'].info(now)
    st.session_state['logger'].info("VERSIONS:")
    st.session_state['logger'].info(f"\tOpenPoliceData: {opd_version}")
    st.session_state['logger'].info(f"\tOPD Explorer: {exp_version}")
    st.session_state['logger'].info(f"\tStreamlit: {st_version}")  # 4/28/2025: Working ver =  1.44.1

def init(level, __version__):
    if 'logger' not in st.session_state:
        st.session_state['logger'] = create_logger(name = 'opd-app', level = level)
        st.session_state['last_selection'] = None
        st.session_state['is_starting_up'] = True  # Indicates that the app has just been instantiated

        st.session_state['logger'].debug("***********DEBUG MODE*************")

    display_version(opd.__version__, __version__, st.__version__)

    
