########################################################################
# 
# gantry_control.sh
#
# Bash script to start gantry_control_init.py
#
# Author: Maria Buechner
#
# History:
# 20.11.2012: started
#
########################################################################
#!/bin/bash


## Set startup on linux machine
#export PYTHONSTARTUP="$HOME\Documents\GantryControl\Python\GantryControl\gantry_control.py"
# Set startup on windows machine
#export PYTHONSTARTUP="$HOME/Desktop/GantryControl/Python/GantryControl/gantry_control.py"
export PYTHONSTARTUP="$HOME/Documents/GantryControl/Python/GantryControl/gantry_control.py"
# Start python
ipython
