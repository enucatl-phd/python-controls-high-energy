import logging

def get_dict(debug):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    return dict(
        version = 1,
        formatters = {
            'f': {'format':
                  '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                 }
        },
        handlers = {
            'h': {
                'class': 'logging.StreamHandler',
                'formatter': 'f',
                'level': level
            }
        },
        root = {
            'handlers': ['h'],
            'level': level,
        },
    )
