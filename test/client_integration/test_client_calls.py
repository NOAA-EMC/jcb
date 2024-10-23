# --------------------------------------------------------------------------------------------------


import copy
import glob
import multiprocessing
import os

import jcb
import pytest
import yaml


# --------------------------------------------------------------------------------------------------


def test_jcb():

    # Get list of apps
    # ----------------
    apps = list(jcb.get_apps())

    # Build list of all the test YAML files
    # -------------------------------------
    app_model_testing_configs = []

    # Look for files in this directory that look like <app>-*-templates.yaml
    # ----------------------------------------------------------------------
    # Loop over apps
    for app in apps:
        path = os.path.join(os.path.dirname(__file__), f'{app}-*-templates.yaml')
        app_model_configs = glob.glob(path)

        # Loop over the configs, open and add for each supported_algorithm
        for app_model_config in app_model_configs:

            with open(app_model_config, 'r') as f:
                dictionary_of_templates = yaml.safe_load(f)

            # Extract the supported_algorithms key and then remove that key from the dictionary
            supported_algorithms = dictionary_of_templates['supported_algorithms']
            del dictionary_of_templates['supported_algorithms']

            # Loop over the supported_algorithms
            for supported_algorithm in supported_algorithms:
                test_dictionary = copy.deepcopy(dictionary_of_templates)
                test_dictionary['algorithm'] = supported_algorithm

                app_model_testing_configs.append(test_dictionary)

    # Call testing with n workers for more speed
    # ------------------------------------------
    n_workers = 6
    with multiprocessing.Pool(processes=n_workers) as pool:
        pool.map(jcb.render_app_with_test_config, app_model_testing_configs)

    # Call in serial (for debugging)
    # ------------------------------
    # for app_model_testing_config in app_model_testing_configs:
        # print(yaml.dump(app_model_testing_config))
        # jcb.render_app_with_test_config(app_model_testing_config)


# --------------------------------------------------------------------------------------------------


# Main entry point
if __name__ == "__main__":
    pytest.main()


# --------------------------------------------------------------------------------------------------
