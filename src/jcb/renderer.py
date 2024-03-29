# --------------------------------------------------------------------------------------------------


import os
import sys

import jcb
import jinja2 as j2
import yaml


# --------------------------------------------------------------------------------------------------


def return_true(obs_type):

    """
    A function that returns True.
    """

    return True


# --------------------------------------------------------------------------------------------------


class Renderer():

    """
    A class to render templates using Jinja2 based on a provided dictionary of templates.

    Attributes:
        template_dict (dict): A dictionary containing the templates and relevant paths.
        j2_search_paths (list): A list of paths where Jinja2 will look for template files.
    """

    def __init__(self, template_dict: dict):

        """
        Initializes the Renderer with a given template dictionary and sets up Jinja2 search paths.

        Args:
            template_dict (dict): A dictionary containing templates and their corresponding paths.
        """

        # Keep the dictionary of templates around
        self.template_dict = template_dict

        # Set the paths where jinja will look for files in the hierarchy
        # --------------------------------------------------------------
        # Set the config path
        config_path = os.path.join(os.path.dirname(__file__), 'configuration')

        # Path with the algorithm files (top level templates)
        self.j2_search_paths = [os.path.join(config_path, 'algorithms')]

        # Path with model files if app needs model things
        app_path_model = self.template_dict.get('app_path_model')
        if app_path_model:

            # Check if app_path_model is an absolute path
            if os.path.isabs(app_path_model):
                self.j2_search_paths += [app_path_model]
            else:
                self.j2_search_paths += [os.path.join(config_path, 'apps', app_path_model)]

        # Path with observation files if app needs obs things
        app_path_observations = self.template_dict.get('app_path_observations')
        if app_path_observations:

            if os.path.isabs(app_path_observations):
                obs_path = app_path_observations
            else:
                obs_path = os.path.join(config_path, 'apps', app_path_observations)

            self.j2_search_paths += [obs_path]

            # Get a list of all the observation files that end in .yaml.j2
            obs_files = [f for f in os.listdir(obs_path) if
                         os.path.isfile(os.path.join(obs_path, f)) and f.endswith('.yaml.j2')]

            # Remove the .yaml.j2 extension from the observation list
            all_observations = [f[:-8] for f in obs_files]

            # If self.template_dict['observations'] is 'all_observations' or ['all_observations']
            # or is not present then replace it with self.template_dict['all_observations']
            if 'observations' not in self.template_dict or \
               self.template_dict['observations'] == 'all_observations' or \
               self.template_dict['observations'] == ['all_observations']:
                self.template_dict['observations'] = all_observations

        # Create the Jinja2 environment
        # -----------------------------
        # print(f'Creating a Jinja2 environment for generating JEDI YAML configuration file. The '
        #       f'following paths will be used for locating templated YAML files: ')
        # for path in self.j2_search_paths:
        #     print(f'  - {path}')

        self.env = j2.Environment(loader=j2.FileSystemLoader(self.j2_search_paths),
                                  undefined=j2.StrictUndefined)

        # Default for the use_observer function in case no chronicle is being used
        self.env.globals['use_observer'] = return_true

        # Path with observation chronicle files
        app_path_observation_chronicle = self.template_dict.get('app_path_observation_chronicle')
        if app_path_observation_chronicle:

            if os.path.isabs(app_path_observation_chronicle):
                path_observation_chronicle = app_path_observation_chronicle
            else:
                path_observation_chronicle = os.path.join(config_path, 'apps',
                                                          app_path_observation_chronicle)

            # print(f'If required an observation chronicle will be used from: ')
            # print(f' - {path_observation_chronicle}')

            # Get window beginning and length from template dictionary
            window_begin = self.template_dict.get('window_begin')
            window_length = self.template_dict.get('window_length')

            # Check that window_begin and window_length are present
            if window_begin is None or window_length is None:
                print('WARNING: The template dictionary is not providing both window_begin and '
                      'window_length so observation chronicle is not active.')
            else:
                # Create the chronicle objects
                self.obs_chron = jcb.ObservationChronicle(path_observation_chronicle, window_begin,
                                                          window_length)

                # Add global function for determining the use of a particular observer.
                self.env.globals['use_observer'] = self.obs_chron.use_observer

                # Add global functions for retrieving the list of all simulated channels
                self.env.globals['get_satellite_simulated_channels'] = \
                    self.obs_chron.get_satellite_simulated_channels
                # Add global functions for retrieving the list of active channels
                self.env.globals['get_satellite_active_channels'] = \
                    self.obs_chron.get_satellite_active_channels
                # Add global functions for retrieving the satellite observation errors
                self.env.globals['get_satellite_observation_errors'] = \
                    self.obs_chron.get_satellite_observation_errors

    # ----------------------------------------------------------------------------------------------

    def render(self, algorithm):

        """
        Renders a given algorithm.

        Args:
            algorithm (str): The name of the algorithm to assemble a YAML for.

        Returns:
            dict: The dictionary that can drive the JEDI executable.
        """

        # print(f'Rendering the JEDI configuration for the {algorithm} algorithm.')

        # Load the algorithm template
        template = self.env.get_template(algorithm + '.yaml.j2')

        # Make sure algorithm is in the template dictionary
        self.template_dict['algorithm'] = algorithm

        # Render the template hierarchy
        try:
            jedi_dict_yaml = template.render(self.template_dict)
        except j2.exceptions.UndefinedError as e:
            print(f'Resolving templates for {algorithm} failed with the following exception: {e}')
            sys.exit(1)

        # Check that everything was rendered
        jcb.abort_if('{{' in jedi_dict_yaml, f'In template_string_jinja2 '
                     f'the output string still contains template directives. '
                     f'{jedi_dict_yaml}')

        jcb.abort_if('}}' in jedi_dict_yaml, f'In template_string_jinja2 '
                     f'the output string still contains template directives. '
                     f'{jedi_dict_yaml}')

        # print(' ')

        # Convert the rendered string to a dictionary
        return yaml.safe_load(jedi_dict_yaml)


# --------------------------------------------------------------------------------------------------


def render(template_dict: dict):

    """
    Creates JEDI executable using only a dictionary of templates.

    Args:
        template_dict (dict): A dictionary that must include an 'algorithm' key among the templates.

    Returns:
        dict: The rendered JEDI dictionary.

    Raises:
        Exception: If the 'algorithm' key is missing in the template dictionary.
    """

    # Create a jcb object
    jcb_object = Renderer(template_dict)

    # Make sure the dictionary of templates has the algorithm key
    jcb.abort_if('algorithm' not in template_dict,
                 'The dictionary of templates must have an algorithm key')

    # Extract algorithm from the dictionary of templates
    algorithm = template_dict['algorithm']

    # Render the jcb object
    return jcb_object.render(algorithm)


# --------------------------------------------------------------------------------------------------
