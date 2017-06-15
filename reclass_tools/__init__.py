import os
import time
import logging.config


LOGGER_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'reclass_tools': {
            'level': 'DEBUG',
            'handlers': ['console_output'],
        },
        'paramiko': {'level': 'WARNING'},
        'iso8601': {'level': 'WARNING'},
        'keystoneauth': {'level': 'WARNING'},
    },
    'handlers': {
        'console_output': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(filename)s:'
                      '%(lineno)d -- %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
}

logging.config.dictConfig(LOGGER_SETTINGS)
# set logging timezone to GMT
logging.Formatter.converter = time.gmtime
logger = logging.getLogger(__name__)
