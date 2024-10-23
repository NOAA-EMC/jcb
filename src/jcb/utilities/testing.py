# --------------------------------------------------------------------------------------------------


import os

import jcb


# --------------------------------------------------------------------------------------------------


def get_apps():

    # Get JCB path
    jcb_path = jcb.get_jcb_path()

    # Path to the apps
    apps_path = os.path.join(jcb_path, 'configuration', 'apps')

    # Return list of apps
    return [app for app in os.listdir(apps_path) if os.path.isdir(os.path.join(apps_path, app))]


# --------------------------------------------------------------------------------------------------


def apps_directory_to_dictionary():

    # Get JCB path
    jcb_path = jcb.get_jcb_path()

    # Path to the apps
    apps_path = os.path.join(jcb_path, 'configuration', 'apps')

    def add_to_dict(d, path_parts, files):
        for part in path_parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[path_parts[-1]] = files

    directory_dict = {}

    for dirpath, _, filenames in os.walk(apps_path):
        yaml_j2_files = [f for f in filenames if f.endswith('.yaml.j2')]
        if yaml_j2_files:
            relative_path = os.path.relpath(dirpath, apps_path)
            path_parts = relative_path.split(os.sep)
            add_to_dict(directory_dict, path_parts, yaml_j2_files)

    return directory_dict


# --------------------------------------------------------------------------------------------------


def render_app_with_test_config(app_test_config):

    # Style 1 for call: all in one API
    # --------------------------------
    jedi_dict_1 = jcb.render(app_test_config)

    # Assert that the output is a dictionary
    # --------------------------------------
    assert isinstance(jedi_dict_1, dict)

    # Style 2 for call: renderer for multiple algorithms
    # --------------------------------------------------
    # Algorithm does not need to be in the dictionary of templates
    algorithm = app_test_config['algorithm']
    del app_test_config['algorithm']

    jcb_obj = jcb.Renderer(app_test_config)
    jedi_dict_2 = jcb_obj.render(algorithm)

    # Assert that the output is a dictionary
    # --------------------------------------
    assert isinstance(jedi_dict_2, dict)

    # Assert that the two outputs match one another
    assert jedi_dict_1 == jedi_dict_2


# --------------------------------------------------------------------------------------------------
