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
import logging

import controls.motors
import controls.eiger
import controls.comet_tube
import controls.log_config

@click.command()
@click.option("-v", "--verbose", count=True)
def main(verbose):
    logger = logging.getLogger()
    logging.config.dictConfig(controls.log_config.get_dict(verbose))
    g0trx = controls.motors.Motor("X02DA-BNK-HE:G0_TRX", "g0trx")
    eiger = controls.eiger.Eiger(
        "129.129.99.99",
        storage_path="/afs/psi.ch/project/hedpc/raw_data/2016/eiger/2016.05.20"
    )
    tube = controls.comet_tube.CometTube()
    IPython.embed()
