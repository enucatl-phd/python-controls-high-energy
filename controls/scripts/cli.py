########################################################################
# Initialize all needed packages and modules
#
# Author: Maria Buechner
#
# History:
# 20.11.2013: started
#
########################################################################

# Imports
import click
import IPython
import logging.config

import controls.motors
import controls.log_config

@click.command()
@click.option("--debug", default=False)
def main(debug):
    logging.config.dictConfig(controls.log_config.get_dict(debug))
    g0trx = controls.motors.Motor("", "")
    IPython.embed()
