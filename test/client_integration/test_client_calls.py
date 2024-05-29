# --------------------------------------------------------------------------------------------------


import copy
import glob
import logging
import multiprocessing
import os

import jcb
import pytest
import yaml


# --------------------------------------------------------------------------------------------------


red = '\033[91m'
end = '\033[0m'


# --------------------------------------------------------------------------------------------------

# Configure logging for multiprocessing
logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.ERROR)


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
    results = []
    with multiprocessing.Pool(processes=n_workers) as pool:
        try:
            results = pool.map(jcb.render_app_with_test_config, app_model_testing_configs)
        except Exception as e:
            pool.terminate()
            pool.join()
            pytest.fail(f"Test failed due to an exception: {e}")
        finally:
            pool.close()
            pool.join()

    # Display any failures
    # --------------------
    if any(isinstance(result, Exception) for result in results):
        print(red+'The following failures were encountered when testing the client calls:'+end)
        for result in results:
            if isinstance(result, Exception):
                print(red+f"  - {result}"+end)
        return 1


# --------------------------------------------------------------------------------------------------


# Main entry point
if __name__ == "__main__":
    test_jcb() #pytest.main()


# --------------------------------------------------------------------------------------------------
