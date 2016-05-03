# 
# cDPC_tomoparams.py
# Parameters for tomographic scans with cDPC setup
# 
#
# Author: Thomas Thuering
#
# History:
# 29.03.2011: first release
#
#################################################################

# Tube settings: 50kV, 80uA
# Talbot-Lau interferometer: p2=2.4um, p1=2.4um, l=100mm, s=200mm
# Alignment: cx = 1044, cy=388, sousam=150mm, soudet=250mm
# height: SAM_TRY = 156.9mm

scanname	= 'phantom_tomo6_' 	#Scan name
start		= 65.0			#piezo start point
end			= 67.4			#piezo end point
nsteps		= 5				#number of phase stepping intervals
exptime		= 18000			#exposure time
samin		= 0.0			#sample in position (Motor: SAM_TRX)
samout		= 40.0			#sample out position (Motor: SAM_TRX)
nproj		= 720			#number of projections
scan360deg	= 1				#360 degree scan on/off
ndarks		= 30			#number of initial darks
nflats		= 36			#number of flatscans for tomography (DPC: evenly distributed over projections)
multiflats	= 4				#number of flats to be acquired during a flatscan (only for dpc_tomoscan)
postflat	= 1				#take one last flat ON/OFF (one additional flat to nflats)
binning		= 1				#binning value
repeats		= 1				#multiple acquisitions per exposure (not integrated automatically)
restart		= 0				#restart on/off
restartfrom	= 650			#restart scan from this projection (index, not angle)
restartto	= 1000			#run scan to this projection after restart (index, not angle)
