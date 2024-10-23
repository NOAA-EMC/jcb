#!/usr/bin/env python


# --------------------------------------------------------------------------------------------------


import os
import sys

import yaml


# --------------------------------------------------------------------------------------------------


if __name__ == "__main__":

    # Get the repo path from the argument
    git_url_in = sys.argv[1]

    # Get the path of this file
    file_path = os.path.dirname(os.path.realpath(__file__))

    # Open the jcb_apps.yaml file
    with open(os.path.join(file_path, 'jcb_clients.yaml')) as file:
        jcb_apps = yaml.load(file, Loader=yaml.FullLoader)

    # Loop over jcb_apps and make sure required keys are present and add target_path
    for app, app_conf in jcb_apps.items():
        if git_url_in.lower() == app_conf['git_url'].lower():
            print(os.path.join(file_path, 'src', 'jcb', 'configuration', 'apps', app))
            exit(0)

    # Fail if we got to here
    exit(1)


# --------------------------------------------------------------------------------------------------
