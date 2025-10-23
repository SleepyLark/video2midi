"""
utils.py - Utility functions for video2midi
Contains helpers for math, key mapping, and general-purpose routines.
"""

import math
import time

def v_rotate(v, ang):
    radAng = ang * math.pi / 180
    return [
        (v[1] * math.cos(radAng)) - (v[0] * math.sin(radAng)),
        (v[1] * math.sin(radAng)) + (v[0] * math.cos(radAng))
    ]

def snap_to_grid(input_value, input_grid_size):
    quantized = int((input_value - int(input_value)) * input_grid_size) / input_grid_size
    result = (quantized + int(input_value))
    return result

def framerate(t0= time.time()-1, frames=0):
    t = time.time()
    frames += 1
    if t - t0 >= 1.0:
        seconds = t - t0
        if seconds != 0:
            fps = frames / seconds
            print(f"{frames:.0f} frames in {seconds:3.1f} seconds = {fps:6.3f} FPS")
        t0 = t
        frames = 0
    return t0, frames



