import logging
from logging.handlers import RotatingFileHandler
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
file_handler = RotatingFileHandler("../bot_log.log", mode='a', maxBytes=1024 * 1024, backupCount=2, encoding=None, delay=0)
file_handler.setFormatter(log_formatter) 
file_handler.setLevel(logging.INFO)

# stdout_handler = logging.StreamHandler()
# stdout_handler.setFormatter(log_formatter)
# stdout_handler.setLevel(logging.INFO)

log = logging.getLogger('root')
log.setLevel(logging.INFO)
log.addHandler(file_handler)

# log.addHandler(stdout_handler)

logging.getLogger('requests').setLevel(logging.CRITICAL)
