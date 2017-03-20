from __future__ import division

import dectris.albula
import logging
import os
import time
import numpy as np

logger = logging.getLogger(__name__)


def dscan(detector, motor, begin, end, intervals, exposure_time=1):
    initial_motor_position = motor.get_current_value()
    logger.debug("initial motor position %s", initial_motor_position)
    try:
        motor.mvr(begin)
        step = (end - begin) / intervals
        detector.setNTrigger(intervals + 1)
        detector.setFrameTime(exposure_time + 0.000020)
        detector.setCountTime(exposure_time)
        detector.arm()
        detector.trigger(exposure_time)
        for i in range(intervals):
            motor.mvr(step)
            time.sleep(0.1)
            logger.info(motor)
            logger.debug("snap %d, detector %s count time, %s frame time",
                i + 1,
                detector.countTime(),
                detector.frameTime(),
                )
            detector.trigger(exposure_time)
        detector.disarm()
        detector.save()
        
    finally:
        logger.debug("going back to initial motor position %s", initial_motor_position)
        motor.mv(initial_motor_position)


def phase_stepping_scan(
        detector, motor, begin, end, intervals,
        phase_stepping_motor, phase_stepping_begin, phase_stepping_end,
        phase_steps, exposure_time=1):
    initial_motor_position = motor.get_current_value()
    initial_phase_stepping_position = phase_stepping_motor.get_current_value()
    logger.debug("initial motor position %s", initial_motor_position)
    logger.debug("initial phase stepping motor position %s",
                 initial_phase_stepping_position)
    try:
        detector.setNTrigger((intervals + 1) * phase_steps)
        detector.setFrameTime(exposure_time + 0.000020)
        detector.setCountTime(exposure_time)
        detector.arm()
        motor_positions = np.linspace(begin, end, intervals + 1)
        phase_stepping_positions = np.linspace(
            phase_stepping_begin,
            phase_stepping_end,
            phase_steps,
            endpoint=False)
        logger.debug(motor_positions)
        logger.debug(phase_stepping_positions)
        for i, motor_position in enumerate(motor_positions):
            motor.mv(initial_motor_position + motor_position)
            logger.debug(motor)
            for phase_stepping_position in phase_stepping_positions:
                phase_stepping_motor.mv(
                    initial_phase_stepping_position + phase_stepping_position)
                detector.trigger(exposure_time)
                logger.debug("step %d, detector %s count time, %s frame time",
                    i + 1,
                    detector.countTime(),
                    detector.frameTime(),
                    )
                logger.debug(phase_stepping_motor)
        detector.disarm()
        detector.save()
        
    finally:
        logger.debug("going back to initial motor position %s", initial_motor_position)
        motor.mv(initial_motor_position)
        phase_stepping_motor.mv(initial_phase_stepping_position)
