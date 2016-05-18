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
import controls.eiger
import controls.log_config

@click.command()
@click.option("--debug", is_flag=True)
def main(debug):
    logging.config.dictConfig(controls.log_config.get_dict(debug))
    g0trx = controls.motors.Motor("X02DA-BNK-HE:G0_TRX", "g0trx")
    eiger = controls.eiger.Eiger("129.129.99.99")
    IPython.embed()
