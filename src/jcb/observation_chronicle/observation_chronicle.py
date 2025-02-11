# --------------------------------------------------------------------------------------------------


from datetime import datetime
import os

import jcb
import yaml


# --------------------------------------------------------------------------------------------------


class ObservationChronicle():

    # ----------------------------------------------------------------------------------------------

    def __init__(self, chronicle_path, window_begin, window_length):

        # Keep the chronicle path
        self.chronicle_path = chronicle_path

        # Convert the window_begin coming in as a string to a datetime object
        self.window_begin = datetime.strptime(window_begin, '%Y-%m-%dT%H:%M:%SZ')

        # Add window_length to window_begin
        self.window_final = self.window_begin + jcb.duration_from_conf(window_length)

        # Save the most recent observer that was passed to the class. This can be used to avoid
        # re-precessing the chronicles if the same observer is used multiple times.
        self.last_observer = ''

        # Read all the chronicles into a dictionary where the key is the observation type and the
        # value is the chronicle dictionary

        # Create dictionary of chronicles
        self.chronicles = {}

        # If path does not exist there are not chronicles for this configuration
        if not os.path.exists(chronicle_path):
            return

        # List all the yaml files in the observation chronicle path
        chronicle_files = [f for f in os.listdir(chronicle_path)
                           if f.endswith('.yaml')]

        # Read each chronicle file
        for chronicle_file in chronicle_files:

            # Read the YAML file
            with open(os.path.join(chronicle_path, chronicle_file), 'r') as file:
                self.chronicles[chronicle_file[:-5]] = yaml.safe_load(file)

    # ----------------------------------------------------------------------------------------------

    def use_observer(self, observer):

        # If there is no chronicle for this type then return True
        if observer not in self.chronicles:
            return True

        # Get the chronicle for the observation type
        obs_chronicle = self.chronicles[observer]

        # Commissioned date
        commissioned = jcb.datetime_from_conf(obs_chronicle.get('commissioned'))

        # Decommissioned date (if present)
        decommissioned_str = obs_chronicle.get('decommissioned', None)
        if decommissioned_str:
            decommissioned = jcb.datetime_from_conf(decommissioned_str)

        # First check that the commissioned period overlaps the window
        # ------------------------------------------------------------

        # If the window does not completely overlap the commissioned period then return False
        if self.window_begin < commissioned:
            return False
        if decommissioned_str and self.window_final > decommissioned:
            return False

        # Observation type dependent checks
        if obs_chronicle['observer_type'] == 'conventional':
            # need to check the use of individual stations/locations
            if not self.get_conventional_rejected_stations(observer):
                return False

        if obs_chronicle['observer_type'] == 'satellite':

            # If there are no simulated channels then return False
            if not self.get_satellite_variable(observer, 'simulated'):
                return False

        # If made it through all the checks then the data is active and should be used
        # ----------------------------------------------------------------------------
        return True

    # ----------------------------------------------------------------------------------------------

    def __process_conventional_stations__(self, observer):

        # Only re-process the chronicle if the observer has changed
        if self.last_observer != observer:

            # Check that there is a chronicle for this type
            jcb.abort_if(observer not in self.chronicles,
                         f"No chronicle found for observation type {observer}. However templates "
                         f"in the observation file require a chronicle.")

            # Get the chronicle for the observation type
            obs_chronicle = self.chronicles[observer]

            # Abort if the window begin is after the decommissioned date
            decommissioned_str = obs_chronicle.get('decommissioned', None)
            if decommissioned_str:
                decommissioned = jcb.datetime_from_conf(decommissioned_str)
                jcb.abort_if(self.window_begin >= decommissioned,
                             f"The window begin is after the decommissioned date for "
                             f"observation type {observer}.")

            # Abort if the type is not conventional
            jcb.abort_if(obs_chronicle['observer_type'] != 'conventional',
                         f"Only conventional observation types are supported. The observation type "
                         f"{observer} is listed as: {obs_chronicle['observer_type']}.")

            # Process the chronicle for this observation type
            self.rejected_station_list = \
                jcb.process_station_chronicles(observer, self.window_begin,
                                               self.window_final, obs_chronicle)

            # Update the last observer
            self.last_observer = observer

        # Return the requested data
        return self.rejected_station_list

    # ----------------------------------------------------------------------------------------------

    def __process_satellite__(self, observer):

        # Only re-process the chronicle if the observer has changed
        if self.last_observer != observer:

            # Check that there is a chronicle for this type
            jcb.abort_if(observer not in self.chronicles,
                         f"No chronicle found for observation type {observer}. However templates "
                         f"in the observation file require a chronicle.")

            # Get the chronicle for the observation type
            obs_chronicle = self.chronicles[observer]

            # Abort if the window begin is after the decommissioned date
            decommissioned_str = obs_chronicle.get('decommissioned', None)
            if decommissioned_str:
                decommissioned = jcb.datetime_from_conf(decommissioned_str)
                jcb.abort_if(self.window_begin >= decommissioned,
                             f"The window begin is after the decommissioned date for "
                             f"observation type {observer}.")

            # Abort if the type is not satellite
            jcb.abort_if(obs_chronicle['observer_type'] != 'satellite',
                         f"Only satellite observation types are supported. The observation type "
                         f"{observer} is listed as: {obs_chronicle['observer_type']}.")

            # Process the satellite chronicle for this observer
            self.sat_variables, self.sat_values = \
                jcb.process_satellite_chronicles(observer, self.window_begin, self.window_final,
                                                 obs_chronicle)

            # Update the last observer
            self.last_observer = observer

        # Return the requested data
        return self.sat_variables, self.sat_values

    # ----------------------------------------------------------------------------------------------

    def get_conventional_rejected_stations(self, observer):

        # Get all the rejected stations for the observation type
        station_list = self.__process_conventional_stations__(observer)

        # force a return of a list of strings since the station IDs have to be strings
        return station_list

    # ----------------------------------------------------------------------------------------------

    def get_satellite_variable(self, observer, variable_name_in):

        # Get all the variables for the satellites
        sat_variables, sat_values = self.__process_satellite__(observer)

        # Assert that 'simulated' is in the variables and get the index
        jcb.abort_if('simulated' not in sat_variables,
                     f"Could not find 'simulated' in the variables for observer {observer}.")
        sim_idx = sat_variables.index('simulated')

        if variable_name_in == 'not_biascorrtd':
            variable_name = 'biascorrtd'
        else:
            variable_name = variable_name_in
        # Assert that variable_name is in the variables and get the index
        jcb.abort_if(variable_name not in sat_variables,
                     f"Could not find '{variable_name}' in "
                     + "the variables for observer {observer}.")
        var_idx = sat_variables.index(variable_name)

        if variable_name_in == 'not_biascorrtd':
            channel_not_bias_corrected = \
                [channel for channel, values in sat_values.items() if not values[var_idx]]
        elif variable_name_in == 'biascorrtd':
            channel_bias_corrected = \
                [channel for channel, values in sat_values.items() if values[var_idx]]
        else:
            # Set variables
            sat_simulated = [channel for channel, values in sat_values.items() if values[sim_idx]]
            sat_variable = [values[var_idx] for _, values in sat_values.items() if values[sim_idx]]

        # Do not return lists, let the YAML developer decide if the variable should be a list or
        # not with use of [] in the YAML. Instead return a comma separated string
        if variable_name_in == 'simulated':
            return ", ".join(str(element) for element in sat_simulated)
        elif variable_name_in == 'not_biascorrtd':
            not_bias_corrected = ", ".join(str(element) for element in channel_not_bias_corrected)
            # Returns a number -999 if all channels are to be bias-corrected. It keeps UFO from
            # skipping bias correction for any channels.
            if not_bias_corrected == "":
                not_bias_corrected = "-999"
            return not_bias_corrected
        elif variable_name_in == 'biascorrtd':
            return ", ".join(str(element) for element in channel_bias_corrected)
        else:
            return ", ".join(str(element) for element in sat_variable)


# --------------------------------------------------------------------------------------------------
