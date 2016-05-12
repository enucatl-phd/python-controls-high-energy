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

import controls.motors


def main():
    g0trx = controls.motors.Motor("", "")
    IPython.embed()


if __name__ == "__main__":
    main()
