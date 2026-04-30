# --------------------------------------------------------------------------------------------------


import os

import jcb
import jinja2 as j2
import yaml
from jcb.observation_chronicle.conv_chronicle import StationID


# --------------------------------------------------------------------------------------------------


def return_true(obs_type):

    """
    A function that returns True.
    """

    return True


# --------------------------------------------------------------------------------------------------


def get_nested_dict(nested_dict, keys):
    for key in keys:
        nested_dict = nested_dict[key]  # Navigate deeper into the dictionary
    return nested_dict


# --------------------------------------------------------------------------------------------------


def _retype_station_id_lists(obj):
    """
    Re-type stations in reject list to StationID type, as type is lost somewhere along the way.
    """
    if isinstance(obj, dict):
        if (isinstance(obj.get('variable'), dict)
                and obj['variable'].get('name') == 'MetaData/stationIdentification'
                and isinstance(obj.get('is_in'), list)):
            obj['is_in'] = [StationID(s) if isinstance(s, str) else s
                            for s in obj['is_in']]
        for v in obj.values():
            _retype_station_id_lists(v)
    elif isinstance(obj, list):
        for item in obj:
            _retype_station_id_lists(item)


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
        algorithm_path_default = os.path.join(config_path, 'algorithms')

        # Check for user provided algorithm path
        algorithm_path = self.template_dict.get('algorithm_path', algorithm_path_default)

        # Load observer_components from the algorithm path
        observer_components = os.path.join(algorithm_path, 'observer_components.yaml')
        with open(observer_components, 'r') as file:
            self.observer_components = yaml.safe_load(file)

        self.j2_search_paths = [algorithm_path]

        # Check to see if there is an app_path_algorithm in the template dictionary
        app_path_algorithm = self.template_dict.get('app_path_algorithm')
        if app_path_algorithm:

            # Check if app_path_algorithm is an absolute path
            if os.path.isabs(app_path_algorithm):
                self.j2_search_paths += [app_path_algorithm]
            else:
                self.j2_search_paths += [os.path.join(config_path, 'apps', app_path_algorithm)]

        # Path with model files if app needs model things
        app_path_model = self.template_dict.get('app_path_model')
        if app_path_model:

            # Take the last element of the path and set this to the model_component in the
            # dictionary. The path might end in a slash so split on / and take the last element.
            self.template_dict['model_component'] = app_path_model.split('/')[-1] + '_'

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

                # Add global functions for retrieving the satellite channel dependant variables
                self.env.globals['get_satellite_variable'] = self.obs_chron.get_satellite_variable

                # Add global functions for retrieving conventional station reject lists
                self.env.globals['get_conventional_rejected_stations'] = \
                    self.obs_chron.get_conventional_rejected_stations

                # Add global functions for testing if the file existed
                self.env.globals['get_obs_engine'] = self.get_obs_engine

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
        except Exception as e:
            msg = f'Resolving templates for {algorithm} failed with the following exception:\n{e}'
            print(msg)
            raise Exception(msg) from e

        # Check that everything was rendered
        jcb.abort_if('{{' in jedi_dict_yaml, f'In template_string_jinja2 '
                     f'the output string still contains template directives. '
                     f'{jedi_dict_yaml}')

        jcb.abort_if('}}' in jedi_dict_yaml, f'In template_string_jinja2 '
                     f'the output string still contains template directives. '
                     f'{jedi_dict_yaml}')

        # print(' ')

        # Convert string form of the dictionary to a dictionary
        jedi_dict = yaml.safe_load(jedi_dict_yaml)

        # Clean up the observers part of the dictionary if necessary. Should only have the
        # components that the algorithm allows for.
        # --------------------------------------------------------------------------------
        # Rename algorithm when running local_ensemble_da_observer and local_ensemble_da_solver
        # to use local_ensemble_da configs in observer_components
        if 'local_ensemble_da' in algorithm:
            algorithm = 'local_ensemble_da'
        if algorithm in self.observer_components:
            # Get the observer components for this algorithm
            observer_location = self.observer_components[algorithm]['observer_nesting']
            allowable_keys = self.observer_components[algorithm]['components']

            # Pointer to observers (mutable list so should not copy here)
            observers = get_nested_dict(jedi_dict, observer_location)

            # Loop over the observers and remove the non allowable components
            for observer in observers:

                observer_keys = observer.keys()

                # Find the observer components that are not allowable
                keys_to_remove = [key for key in observer_keys if key not in allowable_keys]

                # Remove the non allowable components
                for key in keys_to_remove:
                    del observer[key]

            # Option to completely override all filters for a list of observations
            # --------------------------------------------------------------------
            if 'replace_obs_filters' in self.template_dict:

                # Get dictionary replace_obs_filters
                replace_obs_filters_dict = self.template_dict['replace_obs_filters']

                # Get list of observations that have their filters replaced
                obs_to_replace = replace_obs_filters_dict['observations']

                # New filter dictionary
                new_filters = replace_obs_filters_dict.get('override_filters', {})

                # Loop over the observers and replace filters for matching observations
                for observer in observers:
                    # Get the observer name from the rendered observer
                    obs_name = observer['obs space']['name']

                    # Check whether to replace filters for this observation
                    if obs_name not in obs_to_replace:
                        continue

                    # Remove any instance of filters
                    for filter_key in ['obs filters', 'obs prior filters',
                                       'obs post filters', 'obs pre filters']:
                        if filter_key in observer:
                            del observer[filter_key]

                    # Set new entry obs filters with the replace dictionary
                    observer['obs filters'] = new_filters

            # Option to add or override obs distribution and obs localizations
            # in local_ensemble_da
            # --------------------------------------------------------------------
            if 'local_ensemble_da' in algorithm:
                # Currently for the atmosphere only
                # Get dictionary obs_distribution_localizations
                if 'obs_distribution_localizations' in self.template_dict:
                    obs_dist_loc_dict = self.template_dict['obs_distribution_localizations']

                    # Get obs_distribution and obs_localizations
                    obs_dist = obs_dist_loc_dict.get('obs_distribution', {})
                    obs_loc = obs_dist_loc_dict.get('obs_localizations', {})

                    # Loop over the observers and add obs distribution and localizations
                    for observer in observers:
                        observer['obs space']['distribution'] = obs_dist
                        observer['obs localizations'] = obs_loc

                    # Override obs distribution and localizations for matching observations
                    if 'override_obs_distribution_localizations' in self.template_dict:
                        override_obs_dist_loc_dict = self.template_dict[
                                                     'override_obs_distribution_localizations']
                        if override_obs_dist_loc_dict['override']:
                            del override_obs_dist_loc_dict['override']
                            obs_to_override = override_obs_dist_loc_dict.keys()
                            for observer in observers:
                                obs_name = observer['obs space']['name']
                                if obs_name not in obs_to_override:
                                    continue
                                obs_dist_loc_dict = override_obs_dist_loc_dict.get(obs_name, {})
                                obs_dist = obs_dist_loc_dict.get('obs_distribution', {})
                                obs_loc = obs_dist_loc_dict.get('obs_localizations', {})
                                observer['obs space']['distribution'] = obs_dist
                                observer['obs localizations'] = obs_loc
                else:
                    print('WARNING: obs_distribution_localizations in local_ensemble_da is')
                    print('         currently not implemented in jcb for this application')
                    print('         (only foratmoshere now).')


        _retype_station_id_lists(jedi_dict)

        # Convert the rendered string to a dictionary
        return jedi_dict

# --------------------------------------------------------------------------------------------------

    def get_obs_engine(self, observation, component, script_input=None):
        """
        Return obs engine based on whether the file exists or not.
        """
        obsdatain_path = self.template_dict.get(f'{component}_obsdatain_path', None)
        obsdatain_prefix = self.template_dict.get(f'{component}_obsdatain_prefix', None)
        obsdatain_suffix = self.template_dict.get(f'{component}_obsdatain_suffix', None)
        obsdatain_script_path = self.template_dict.get(f'{component}_obsdatain_script_path', None)
        obs_engine = None
        if obsdatain_path and obsdatain_prefix and obsdatain_suffix:
            obsdatain_filename = os.path.join(
                obsdatain_path,
                f"{obsdatain_prefix}{observation}{obsdatain_suffix}"
            )
            if os.path.exists(obsdatain_filename):
                obs_engine = dict(type='H5File', obsfile=obsdatain_filename)
            else:
                if obsdatain_script_path and script_input:
                    obs_engine = {
                        'type': 'script',
                        'script file': os.path.join(obsdatain_script_path,
                                                    f'{observation.split("_")[0]}.py'),
                        'args': {'input': script_input},
                        'category': observation.split('_')[-1]
                    }
        if obs_engine:
            return obs_engine
        else:
            jcb.abort(
                f"Missing or invalid input: obsdatain_path={obsdatain_path}, "
                f"prefix={obsdatain_prefix}, suffix={obsdatain_suffix}, "
                f"script_path={obsdatain_script_path}, or file not found: "
                f"{obsdatain_filename if obsdatain_filename is not None else 'N/A'}"
            )


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
