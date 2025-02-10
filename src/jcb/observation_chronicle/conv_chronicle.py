# --------------------------------------------------------------------------------------------------


import copy
from datetime import datetime

import jcb


# --------------------------------------------------------------------------------------------------

"""
Function mapping for variable strategy. If the channel values vary over the window because a
chronicle happens during that window you need a strategy to choose the value. For example, for the
variables that determine if a channel is used or not, min is likely a sensible strategy.
This will ensure the channel is completely off for that window and no bad data can make it in.
If the variable is error it may be better to choose max as the strategy to ensure the maximum
needed error is chosen over the window. If other functions are needed in the future they can be
added here. In the YAML the user defined the strategy as a string so this dictionary provides a
map to the actual functions.
"""

function_map = {
    'min': min,
    'max': max,
}


# --------------------------------------------------------------------------------------------------

def process_station_chronicles(ob_type, window_begin, window_final, chronicle_in):
    print('hello world')
    return {}

# --------------------------------------------------------------------------------------------------
