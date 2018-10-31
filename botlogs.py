import logging
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter("%(asctime)s - %(module)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s")
file_handler = RotatingFileHandler("../bot_log.log", mode='ba', maxBytes=1024 * 1024, backupCount=2, encoding='utf-8', delay=0)
file_handler.setFormatter(log_formatter) 
file_handler.setLevel(logging.INFO)

log = logging.getLogger('root')
log.setLevel(logging.INFO)
log.addHandler(file_handler)

logging.getLogger('requests').setLevel(logging.CRITICAL)
