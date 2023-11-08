from enum import Enum
import logging
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
import types


def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip


class Code(Enum):
    SUBTABLE_MENU = 1
    NO_SUBTABLE_MENU = 2
    SINGLE_YEAR_DATA = 3
    MULTIYEAR_DATA = 4
    NA_YEAR_DATA = 5
    MULTIPLE_MULTIYEAR_DATA = 6  # Don't think we have any of this right now
    GET_AGENCIES = 7
    CHANGE_SELECTION = 8
    SINGLE_AGENCY_SELECT = 9
    FETCH_DATA_GET_COUNT = 10
    FETCH_DATA_LOAD_WO_COUNT = 11
    FETCH_DATA_LOAD_WITH_COUNT = 12
    PREVIEW_REGEXREP_SUCCESS = 13
    DOWNLOAD = 14
    MULTIYEAR_FILE = 15

# https://discuss.streamlit.io/t/streamlit-duplicates-log-messages-when-stream-handler-is-added/16426/4
def create_logger(name, level=logging.INFO, file=None, addtime=False):
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    if addtime:
        format = "%(asctime)s :: %(message)s"
    else:
        format = '%(message)s'
    #if no streamhandler present, add one
    if sum([isinstance(handler, logging.StreamHandler) for handler in logger.handlers]) == 0:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(format, '%y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)
    #if a file handler is requested, check for existence then add
    if file is not None:
        if sum([isinstance(handler, logging.FileHandler) for handler in logger.handlers]) == 0:
            ch = logging.FileHandler(file, 'w')
            ch.setFormatter(logging.Formatter(format, '%y-%m-%d %H:%M:%S'))
            logger.addHandler(ch)

    if level <= logging.DEBUG:
        logger.code_segments = [e for e in Code]

    def code_reached(self, code):
        if level <= logging.DEBUG:
            if code in self.code_segments:
                self.code_segments.remove(code)

    def log_coverage(self):
        if level <= logging.DEBUG:
            if len(self.code_segments)>0:
                self.debug(f"Remaining debug events: {self.code_segments}")
            else:
                self.debug("No remaining debug events")

    # Add method to logger object
    logger.code_reached = types.MethodType(code_reached, logger)
    logger.log_coverage = types.MethodType(log_coverage, logger)
        
    return logger
