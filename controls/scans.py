from __future__ import division

import dectris.albula
import logging
import os
import time

logger = logging.getLogger(__name__)


def dscan(detector, motor, begin, end, intervals, exposure_time=1):
    initial_motor_position = motor.get_current_value()
    logger.debug("initial motor position %s", initial_motor_position)
    try:
        motor.mvr(begin)
        step = (end - begin) / intervals
        detector.setNImages(intervals + 1)
        detector.setFrameTime(exposure_time + 0.000020)
        detector.setCountTime(exposure_time)
        detector.arm()
        detector.trigger()
        time.sleep(exposure_time)
        for _ in range(intervals):
            motor.mvr(step)
            logger.info(motor)
            logger.debug("detector %s count time, %s frame time",
                detector.frameTime(),
                detector.countTime())
            detector.trigger()
            time.sleep(exposure_time)
        detector.disarm()
        detector.save()
    finally:
        logger.debug("going back to initial motor position %s", initial_motor_position)
        motor.mv(initial_motor_position)
