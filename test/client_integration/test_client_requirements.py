# --------------------------------------------------------------------------------------------------


import os
import re

import jcb
import pytest


# --------------------------------------------------------------------------------------------------


red = '\033[91m'
end = '\033[0m'


# --------------------------------------------------------------------------------------------------


'''
Clients that attach to JCB have to meet various requirements in order to pass the following tests.

1. Files in the model/<component> directory of the application must only use keys (templates) that
   start with <component>_, to avoid ambiguity when multiple model components are being used.

2. Files in the model/<component> directory of the application must start with <component>_ to
   avoid ambiguity when multiple model components are being used.

3. Only files in the observation directory are allowed to make use of YAML anchors and the anchors
   must include the observation name to avoid ambiguity.

4. Each app directory can only contain directories with certain names, given by the
   allowable_dirs list.
'''


# --------------------------------------------------------------------------------------------------


def test_model_files_have_prepended_templates():

    # Get dictionary of all apps and Jinja2 files
    apps_directory_dict = jcb.apps_directory_to_dictionary()

    # Message to write if an error is found
    message = red + '\n\n' + '''
        YAML files in the model directory of the JCB client must only use keys (templates) that
        start with <model>_. This is to ensure that no two model components are making use of the
        same template keys. Otherwise the template mechanism in JCB would be ambiguous when, for
        example, strongly coupled data assimilation is being configured.
    ''' + '\n\n' + end

    # Loop over the apps
    for app, app_dirs in apps_directory_dict.items():

        app_components = list(app_dirs.keys())

        # Check for the use of anchors in the mode directory
        # --------------------------------------------------
        if 'model' in app_components:

            app_model_components = list(app_dirs['model'].keys())

            model_components_template_keys = {}

            for app_model_component in app_model_components:

                model_components_template_keys[app_model_component] = []

                app_model_component_files = app_dirs['model'][app_model_component]

                # Loop over the files, open them and check for YAML anchors.
                template_keys = []
                for file in app_model_component_files:

                    file_path = os.path.join(jcb.get_jcb_path(), 'configuration', 'apps', app,
                                             'model', app_model_component, file)

                    # Open file as a string
                    with open(file_path, 'r') as f:
                        file_string = f.read()

                    # Get every instance of {{...}} in the file
                    template_keys = re.findall(r'{{(.*?)}}', file_string)

                    # Remove anything after the first |
                    template_keys = [key.split('|')[0] for key in template_keys]

                    # Remove whitespace from the keys
                    template_keys = [key.replace(" ", "") for key in template_keys]

                    # Check that every element of template_keys starts with app_model_component_
                    for key in template_keys:
                        assert key.split('_')[0] == app_model_component, \
                            f"{message} Template key {key} in file {file} in app {app}/model/" + \
                            f"{app_model_component} does not start with {app_model_component}_."


# --------------------------------------------------------------------------------------------------


def test_model_files_are_prepended():

    # Get dictionary of all apps and Jinja2 files
    apps_directory_dict = jcb.apps_directory_to_dictionary()

    # Message to write if an error is found
    message = red + '\n\n' + '''
        YAML files in the model directory of the JCB client must start with <model>_. This is to
        ensure that no two model component files have the same name. Otherwise the template
        mechanism in JCB would not know which file to choose when multiple model directories are
        provided, for example when strongly coupled data assimilation is being configured.
    ''' + '\n\n' + end

    # Loop over the apps
    for app, app_dirs in apps_directory_dict.items():

        app_components = list(app_dirs.keys())

        # Check for the use of anchors in the mode directory
        # --------------------------------------------------
        if 'model' in app_components:

            app_model_components = list(app_dirs['model'].keys())

            for app_model_component in app_model_components:

                app_model_component_files = app_dirs['model'][app_model_component]

                # Loop over the files, open them and check for YAML anchors.
                for file in app_model_component_files:

                    # Split name by underscore and check that the first element is 'model'
                    assert file.split('_')[0] == app_model_component, \
                        f"{message} Model file {file} in app {app}/model/{app_model_component} " + \
                        f"does not start with {app_model_component}_."


# --------------------------------------------------------------------------------------------------


def test_check_for_yaml_anchors():

    # Get JCB path
    jcb_path = jcb.get_jcb_path()

    # Path to the apps
    apps_path = os.path.join(jcb_path, 'configuration', 'apps')

    # Get dictionary of all apps and Jinja2 files
    apps_directory_dict = jcb.apps_directory_to_dictionary()

    # Message to write if an error is found
    message = red + '\n\n' + '''
        Using YAML anchors can be dangerous! JCB treats YAML files as strings so they an be
        templated. When combining YAMLs from different places as strings the use of anchors may
        have unpredictable behavior and may not be properly resolved. JCB currently disallows
        anchors in the model directory. JCB allows anchors in the observation directory but the
        anchor must include the templated {{observation_from_jcb}} element to ensure uniqueness.
    ''' + '\n\n' + end

    # Loop over the apps
    for app, app_dirs in apps_directory_dict.items():

        app_components = list(app_dirs.keys())

        # Check for the use of anchors in the mode directory
        # --------------------------------------------------

        if 'model' in app_components:

            app_model_components = list(app_dirs['model'].keys())

            for app_model_component in app_model_components:

                app_model_component_files = app_dirs['model'][app_model_component]

                # Loop over the files, open them and check for YAML anchors.
                for app_model_component_file in app_model_component_files:

                    file = os.path.join(apps_path, app, 'model', app_model_component,
                                        app_model_component_file)

                    # Open file as a string
                    with open(file, 'r') as f:
                        file_string = f.read()

                    # Loop over lines and remove all whitespace from the line. Check that :&
                    # and :* are not present anywhere in the file.
                    for line in file_string.split('\n'):
                        line = line.replace(" ", "")
                        assert ':&' not in line, f"{message} Anchor found in {file}. Line: {line}"
                        assert ':*' not in line, f"{message} Anchor found in {file}. Line: {line}"

        # Now check for the use of anchors in the observation directory
        # -------------------------------------------------------------

        if 'observations' in app_components:

            app_obs_components = list(app_dirs['observations'].keys())

            for app_obs_component in app_obs_components:

                app_obs_component_files = app_dirs['observations'][app_obs_component]

                # Loop over the files, open them and check for YAML anchors.
                for app_obs_component_file in app_obs_component_files:

                    file = os.path.join(apps_path, app, 'observations', app_obs_component,
                                        app_obs_component_file)

                    # Open file as a string
                    with open(file, 'r') as f:
                        file_string = f.read()

                    # Loop over lines and remove all whitespace from the line. Check that :&
                    # and :* are not present anywhere in the file.
                    for line in file_string.split('\n'):
                        line = line.replace(" ", "")

                        # Replace <anchor>{{observation_from_jcb}} since this is a valid anchor.
                        line = line.replace('&{{observation_from_jcb}}', '')
                        line = line.replace('*{{observation_from_jcb}}', '')

                        assert ':&' not in line, f"{message} Anchor found in {file}. Line: {line}"
                        assert ':*' not in line, f"{message} Anchor found in {file}. Line: {line}"


# --------------------------------------------------------------------------------------------------

def test_client_allowable_components():

    # Get JCB path
    jcb_path = jcb.get_jcb_path()

    # List of apps is list of dirs in path_to_apps (e.g. gdas)
    apps = jcb.get_apps()

    # Optional directories for the application
    allowable_dirs = [
        '.github',
        'model',
        'observations',
        'algorithm',
        'observation_chronicle',
        'test',
        ]

    # Loop over the apps
    for app in apps:

        # Path to the app
        app_path = os.path.join(jcb_path, 'configuration', 'apps', app)

        # Check that the directories within each app directory are allowable
        app_dirs = [d for d in os.listdir(app_path) if os.path.isdir(os.path.join(app_path, d))]

        # Check that all directories are allowable
        for d in app_dirs:
            assert d in allowable_dirs, f"Directory {d} is not allowable for app {app}."


# -------------------------------------------------------------------------------------------------


# Main entry point
if __name__ == "__main__":
    pytest.main()


# --------------------------------------------------------------------------------------------------
