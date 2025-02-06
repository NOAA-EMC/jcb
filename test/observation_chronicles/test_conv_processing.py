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

observer_type: conventional  # Type of chronicle to use

# observation type initial configuration
# --------------------------------
reject_list: ['KBWI']

# Chronicle of changes for this observation type
# ----------------------------------------
chronicles:

- action_date: "2009-12-22T00:00:00"
  justification: 'I do not like DCA anymore'
  add_to_reject_list: ['KDCA']

- action_date: "2009-12-25T00:00:00"
  justification: 'I now like BWI'
  remove_from_reject_list: ['KBWI']
"""

# Read the YAML file into a dictionary
conv_chronicle = yaml.safe_load(config_file)


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
