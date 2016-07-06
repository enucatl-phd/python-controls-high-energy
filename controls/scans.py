from __future__ import division

import dectris.albula
import logging
import os

logger = logging.getLogger(__name__)


def dscan(detector, motor, begin, end, intervals, exposure_time=1):
    initial_motor_position = motor.get_current_value()
    try:
        motor.mvr(begin)
        step = (end - begin) / intervals
        detector.setNImages(intervals + 1)
        detector.setFrameTime(exposure_time + 0.000020)
        detector.setCountTime(exposure_time)
        detector.arm()
        detector.trigger()
        for _ in range(intervals):
            motor.mvr(step)
            logger.info(motor)
            detector.trigger()
        detector.disarm()
        detector.save()
    finally:
        motor.mv(initial_motor_position)
