def get_dict(verbose):
    levels = [
        'INFO',
        'DEBUG',
    ]
    verbose = min(len(levels) - 1, verbose)
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
            }
        },
        root = {
            'handlers': ['h'],
            'level': levels[verbose],
        },
    )
