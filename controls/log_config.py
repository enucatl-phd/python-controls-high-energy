def get_dict(debug):
    if debug:
        level = 'DEBUG'
    else:
        level = 'ERROR'
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
                'level': level
            }
        },
        root = {
            'handlers': ['h'],
            'level': level,
        },
    )
