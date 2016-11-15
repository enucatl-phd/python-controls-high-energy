import os
import datetime


def get_dict(verbose):
    levels = [
        'INFO',
        'DEBUG',
    ]
    verbose = min(len(levels) - 1, verbose)
    now = datetime.datetime.now()
    file_name = "log/bunker4controls.logfile.{0}.log.bz2".format(now.strftime("%y%m%d.%H%M%S%f"))
    if not os.path.isdir("log"):
        os.makedirs("log")
    return dict(
        version = 1,
        disable_existing_loggers = False,
        formatters = {
            'f': {'format':
                  '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                 }
        },
        handlers = {
            'h': {
                'class': 'logging.StreamHandler',
                'formatter': 'f',
                'level': levels[verbose],
            },
            'logfile': {
                'class': 'logging.FileHandler',
                'formatter': 'f',
                'level': levels[verbose],
                'filename': file_name,
                'mode': 'w',
                'encoding': 'bz2',
            }
        },
        root = {
            'handlers': ['h', 'logfile'],
            'level': levels[verbose],
        },
    )
