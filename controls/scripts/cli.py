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
import controls.remote_detector
import controls.pilatus
import controls.hamamatsu_flat_panel
import controls.comet_tube
import controls.scans
import controls.log_config

@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("-s", "--storage_path",
    default="/afs/psi.ch/project/hedpc/raw_data/2016/pilatus/2016.07.19",
    type=click.Path(exists=True))
@click.option("-t", "--threshold",
    default=10000,
    help="detector threshold energy (eV)")
def main(verbose, storage_path, threshold):
    logger = logging.getLogger()
    logging.config.dictConfig(controls.log_config.get_dict(verbose))
    g0trx = controls.motors.Motor("X02DA-BNK-HE:G0_TRX", "g0trx")
    g0try = controls.motors.Motor("X02DA-BNK-HE:G0_TRY", "g0try")
    g0trz = controls.motors.Motor("X02DA-BNK-HE:G0_TRZ", "g0trz")
    g0rotx = controls.motors.Motor("X02DA-BNK-HE:G0_ROTX", "g0rotx")
    g0roty = controls.motors.Motor("X02DA-BNK-HE:G0_ROTY", "g0roty")
    g0rotz = controls.motors.Motor("X02DA-BNK-HE:G0_ROTZ", "g0rotz")
    g1trx = controls.motors.Motor("X02DA-BNK-HE:G1_TRX", "g1trx")
    g1try = controls.motors.Motor("X02DA-BNK-HE:G1_TRY", "g1try")
    g1trz = controls.motors.Motor("X02DA-BNK-HE:G1_TRZ", "g1trz")
    g1rotx = controls.motors.Motor("X02DA-BNK-HE:G1_ROTX", "g1rotx")
    g1roty = controls.motors.Motor("X02DA-BNK-HE:G1_ROTY", "g1roty")
    g1rotz = controls.motors.Motor("X02DA-BNK-HE:G1_ROTZ", "g1rotz")
    g2trx = controls.motors.Motor("X02DA-BNK-HE:G2_TRX", "g2trx")
    g2try = controls.motors.Motor("X02DA-BNK-HE:G2_TRY", "g2try")
    g2trz = controls.motors.Motor("X02DA-BNK-HE:G2_TRZ", "g2trz")
    g2rotx = controls.motors.Motor("X02DA-BNK-HE:G2_ROTX", "g2rotx")
    g2roty = controls.motors.Motor("X02DA-BNK-HE:G2_ROTY", "g2roty")
    g2rotz = controls.motors.Motor("X02DA-BNK-HE:G2_ROTZ", "g2rotz")
    smpltrx = controls.motors.Motor("X02DA-BNK-HE:SMPL_TRX", "smpltrx")
    smpltry = controls.motors.Motor("X02DA-BNK-HE:SMPL_TRY", "smpltry")
    smplroty = controls.motors.Motor("X02DA-BNK-HE:SMPL_ROTY", "smplroty")
    stptrx = controls.motors.Motor("X02DA-BNK-HE:STP_TRX", "stptrx")
    detector = controls.remote_detector.RemoteDetector(
        "129.129.99.96",
        storage_path=storage_path,
        photon_energy=[threshold, 2*threshold]
    )
    # detector = controls.eiger.Eiger(
        # "129.129.99.112",
        # storage_path=storage_path,
        # photon_energy=threshold
    # )
    # detector = controls.pilatus.Pilatus(
     #   "129.129.99.81",
      #  storage_path=storage_path,
       # photon_energy=threshold
    # )
    tube = controls.comet_tube.CometTube()
    IPython.embed()
