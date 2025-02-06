# --------------------------------------------------------------------------------------------------


import copy
from datetime import datetime

import jcb
import pytest
import yaml


# --------------------------------------------------------------------------------------------------


# YAML File for testing

config_file = """
# Instrument metadata
# -------------------
commissioned: 2009-04-14T00:00:00

observer_type: satellite  # Type of chronicle to use

# Instrument initial configuration
# --------------------------------
channel_variables:
  simulated: min
  active: min
  error: max
channel_values:
  1:  [ 1,  1,  2.50 ]
  2:  [ 1,  1,  2.20 ]
  3:  [ 1,  1,  2.00 ]
  4:  [ 1,  1,  0.55 ]

# Chronicle of changes for this instrument
# ----------------------------------------
chronicles:

- action_date: "2009-04-20T00:00:00"
  justification: 'Example of making a channel inactive'
  channel_values:
    2:  [ 1,  -1,  2.20 ]

- action_date: "2009-04-22T00:00:00"
  justification: 'Example of removing a channel completely'
  channel_values:
    4:  [ 0,  1,  0.55 ]

- action_date: "2009-04-24T00:00:00"
  justification: 'Example of deactivating all channels'
  adjust_variable_for_all_channels:
    variables: [simulated, active]
    values: [0, -1]

- action_date: "2009-04-26T00:00:00"
  justification: 'Example of reactivating all channels'
  revert_to_previous_date_time: "2009-04-23T00:00:00"  # Note that the datetime does not have
                                                       # to match an action_date

- action_date: "2009-04-28T00:00:00"
  justification: 'Example of increasing error'
  channel_values:
    1:  [ 1,  1,  4.50 ]
"""

# Read the YAML file into a dictionary
satellite_chronicle = yaml.safe_load(config_file)


# --------------------------------------------------------------------------------------------------


def test_window_before_chronicles():

    window_begin = datetime.fromisoformat("2009-04-15T00:00:00")
    window_final = datetime.fromisoformat("2009-04-15T06:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [1, 1, 2.5], 2: [1, 1, 2.2], 3: [1, 1, 2.0], 4: [1, 1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_window_after_chronicles():

    window_begin = datetime.fromisoformat("2010-01-01T00:00:00")
    window_final = datetime.fromisoformat("2010-01-01T06:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [1, 1, 4.5], 2: [1, -1, 2.2], 3: [1, 1, 2.0], 4: [0, 1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_window_straddles_chronicle():

    # With min strategy
    # -----------------
    window_begin = datetime.fromisoformat("2009-04-19T21:00:00")
    window_final = datetime.fromisoformat("2009-04-20T03:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [1, 1, 2.5], 2: [1, -1, 2.2], 3: [1, 1, 2.0], 4: [1, 1, 0.55]}
    assert channel_values == expected

    # With max strategy
    # -----------------
    window_begin = datetime.fromisoformat("2009-04-27T21:00:00")
    window_final = datetime.fromisoformat("2009-04-28T03:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [1, 1, 4.5], 2: [1, -1, 2.2], 3: [1, 1, 2.0], 4: [0, 1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_everything_deactivated():

    window_begin = datetime.fromisoformat("2009-04-24T00:00:00")
    window_final = datetime.fromisoformat("2009-04-24T03:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [0, -1, 2.5], 2: [0, -1, 2.2], 3: [0, -1, 2.0], 4: [0, -1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_still_deactivated():

    window_begin = datetime.fromisoformat("2009-04-25T18:00:00")
    window_final = datetime.fromisoformat("2009-04-26T00:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [0, -1, 2.5], 2: [0, -1, 2.2], 3: [0, -1, 2.0], 4: [0, -1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_everything_reverted():

    window_begin = datetime.fromisoformat("2009-04-26T00:00:00")
    window_final = datetime.fromisoformat("2009-04-26T01:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         satellite_chronicle)

    # Check against expected output
    expected = {1: [1, 1, 2.5], 2: [1, -1, 2.2], 3: [1, 1, 2.0], 4: [0, 1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


def test_no_chronicles():

    # Copy the chronicle and remove the chronicles
    no_chronicles = copy.deepcopy(satellite_chronicle)
    del no_chronicles['chronicles']

    window_begin = datetime.fromisoformat("2010-01-01T00:00:00")
    window_final = datetime.fromisoformat("2010-01-01T06:00:00")

    _, channel_values = jcb.process_satellite_chronicles('test_sat', window_begin, window_final,
                                                         no_chronicles)

    # Check against expected output
    expected = {1: [1, 1, 2.5], 2: [1, 1, 2.2], 3: [1, 1, 2.0], 4: [1, 1, 0.55]}
    assert channel_values == expected


# --------------------------------------------------------------------------------------------------


# Main entry point
if __name__ == "__main__":
    pytest.main()


# --------------------------------------------------------------------------------------------------
