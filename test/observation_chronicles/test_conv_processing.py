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

window_option: max

# observation type initial configuration
# --------------------------------
stations_to_reject: ['KBWI', 'KIAD']

# Chronicle of changes for this observation type
# ----------------------------------------
chronicles:

- action_date: "2009-12-22T00:00:00"
  justification: 'I do not like DCA anymore'
  add_to_reject_list: ['KDCA']

- action_date: "2009-12-25T00:00:00"
  justification: 'I now like BWI'
  remove_from_reject_list: ['KBWI']

- action_date: "2009-12-26T00:00:00"
  justification: 'I do not like CGS anymore'
  add_to_reject_list: ['KCGS']

"""

# Read the YAML file into a dictionary
conv_chronicle = yaml.safe_load(config_file)


# --------------------------------------------------------------------------------------------------


def test_window_before_chronicles():

    window_begin = datetime.fromisoformat("2009-04-15T00:00:00")
    window_final = datetime.fromisoformat("2009-04-15T06:00:00")

    station_list = jcb.process_station_chronicles('test_adpsfc', window_begin, window_final,
                                                         conv_chronicle)

    # Check against expected output
    expected = ['KBWI', 'KIAD']
    assert station_list == expected


# --------------------------------------------------------------------------------------------------


def test_window_after_chronicles():

    window_begin = datetime.fromisoformat("2010-01-01T00:00:00")
    window_final = datetime.fromisoformat("2010-01-01T06:00:00")

    station_list = jcb.process_station_chronicles('test_adpsfc', window_begin, window_final,
                                                         conv_chronicle)

    # Check against expected output
    expected = ['KIAD', 'KDCA', 'KCGS']
    assert station_list == expected


# --------------------------------------------------------------------------------------------------


def test_window_straddles_chronicle():

    # With max strategy
    # -----------------
    window_begin = datetime.fromisoformat("2009-12-24T21:00:00")
    window_final = datetime.fromisoformat("2009-12-25T03:00:00")

    station_list = jcb.process_station_chronicles('test_adpsfc', window_begin, window_final,
                                                         conv_chronicle)

    # Check against expected output
    expected = ['KIAD', 'KDCA']
    assert station_list == expected


# --------------------------------------------------------------------------------------------------


def test_no_chronicles():

    # Copy the chronicle and remove the chronicles
    no_chronicles = copy.deepcopy(conv_chronicle)
    del no_chronicles['chronicles']

    window_begin = datetime.fromisoformat("2010-01-01T00:00:00")
    window_final = datetime.fromisoformat("2010-01-01T06:00:00")

    station_list = jcb.process_station_chronicles('test_adpsfc', window_begin, window_final,
                                                         no_chronicles)

    # Check against expected output
    expected = ['KBWI', 'KIAD']
    assert station_list == expected


# --------------------------------------------------------------------------------------------------


# Main entry point
if __name__ == "__main__":
    pytest.main()


# --------------------------------------------------------------------------------------------------
