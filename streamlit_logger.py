import logging

# https://discuss.streamlit.io/t/streamlit-duplicates-log-messages-when-stream-handler-is-added/16426/4
def create_logger(name, level='INFO', file=None, addtime=False):
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
        
    return logger
