# --------------------------------------------------------------------------------------------------


import os

from .observation_chronicle.observation_chronicle import ObservationChronicle
from .observation_chronicle.satellite_chronicle import process_satellite_chronicles
from .observation_chronicle.conv_chronicle import process_station_chronicles
from .renderer import render as render
from .renderer import Renderer as Renderer
from .utilities.config_parsing import datetime_from_conf, duration_from_conf
from .utilities.parse_channels import parse_channels, parse_channels_set
from .utilities.testing import get_apps, apps_directory_to_dictionary, render_app_with_test_config
from .utilities.trapping import abort, abort_if


# --------------------------------------------------------------------------------------------------


# JCB Version
__version__ = '0.1.0'


def version():
    return __version__


# --------------------------------------------------------------------------------------------------


# Define the visible functions and classes
__all__ = [
    'Renderer',
    'render',
    'ObservationChronicle',
    'process_satellite_chronicles',
    'process_station_chronicles',
    'datetime_from_conf',
    'duration_from_conf',
    'parse_channels',
    'parse_channels_set',
    'abort_if',
    'abort',
    'version',
    '__version__',
    'get_jcb_path',
    'get_apps',
    'apps_directory_to_dictionary',
    'render_app_with_test_config',
]


# --------------------------------------------------------------------------------------------------


# Function that returns the path of the this file
def get_jcb_path():
    return os.path.dirname(os.path.realpath(__file__))


# --------------------------------------------------------------------------------------------------
