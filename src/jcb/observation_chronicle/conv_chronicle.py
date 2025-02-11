# --------------------------------------------------------------------------------------------------


import copy
from datetime import datetime

import jcb


# --------------------------------------------------------------------------------------------------

"""
Function mapping for variable strategy. If the channel values vary over the window because a
chronicle happens during that window you need a strategy to choose the value. For example, for the
variables that determine if a channel is used or not, min is likely a sensible strategy.
This will ensure the channel is completely off for that window and no bad data can make it in.
If the variable is error it may be better to choose max as the strategy to ensure the maximum
needed error is chosen over the window. If other functions are needed in the future they can be
added here. In the YAML the user defined the strategy as a string so this dictionary provides a
map to the actual functions.
"""

function_map = {
    'min': min,
    'max': max,
}


# --------------------------------------------------------------------------------------------------


def add_to_evolving_observing_system(evolving_observing_system, datetime, station_reject_list):

    """
    Add the rejected station IDs to the evolving observing system. This function is used to add the
    station IDs to the evolving observing system. The evolving observing system is a list of
    dictionaries where each dictionary has a datetime key and a station_reject_list key.
    The datetime key is a datetime object and the station_reject_list key is a list of strings
    of station IDs that are to be rejected by quality control procedures.

    Args:
        evolving_observing_system (list): The evolving observing system.
        datetime (datetime): The datetime of the station IDs.
        station_reject_list (list): List of strings of station IDs.

    Returns:
        None (None): Mutable evolving_observing_system is updated in place.
    """

    # Temporary dictionary
    temp_dict = {}
    temp_dict['datetime'] = copy.deepcopy(datetime)
    temp_dict['station_reject_list'] = copy.deepcopy(station_reject_list)

    # Append to the evolving observing system
    evolving_observing_system.append(temp_dict)


# --------------------------------------------------------------------------------------------------


def get_left_index(error_message, action_dates, insert_point):

    """
    Get the index of the nearest action date that is before or equal to the insert point. This
    function finds the index of the nearest action date that is before or equal to the insert point.
    If the insert point is before the first action date then None is returned.

    Args:
        action_dates (list): A list of action dates.
        insert_point (datetime): The insert point.

    Returns:
        int: The index of the nearest action date that is before or equal to the insert point.
    """

    # Abort if the insert point is before the first action date
    jcb.abort_if(insert_point < action_dates[0],
                 f"{error_message} The insert point is before the first action date.")

    # Find the index of the nearest action date that is before or equal to the insert point
    for index, action_date in enumerate(action_dates):
        if action_date <= insert_point:
            index_of_previous = index
        else:
            break

    return index_of_previous


# --------------------------------------------------------------------------------------------------


def process_station_chronicles(ob_type, window_begin, window_final, chronicle_in):

    """
    Process conventional observation station chronicles for a specified time window, determining
    which station IDs should be included in the reject list based on the chronicle's actions.

    This function iterates through an observation type's chronological data records, adjusting
    the station reject list as dictated by the chronicles. It validates the chronicle structure,
    ensures chronological order, and applies adjustments or reverts as specified. The final output
    is a set of station IDs adjusted according to the specified window and strategies.

    Args:
        window_begin (datetime): The beginning of the data assimilation window.
        window_final (datetime): The end of the data assimilation window.
        chronicle (dict): A dictionary containing the observation type's commissioning data,
                          station reject list, and a list of chronological actions (chronicles) that
                          include  adjustments or reverts of station IDs.

    Returns:
        list: A list of strings of station IDs that should be included in a reject list
              according to the specified time window and the strategies chosen
              for variable adjustments.

    Raises:
        AbortException: If any of the preconditions are not met.

    Note:
        The function assumes that the station IDs are properly structured
        in the input `chronicle` dictionary.
    """

    # Copy the incoming chronicle to avoid modifying the original
    # -----------------------------------------------------------
    chronicle = copy.deepcopy(chronicle_in)

    # Create a message to prepend any errors with
    # -------------------------------------------
    errors_message_pre = f"Error processing station reject list chronicle for {ob_type}"

    # Commissioned time for this platform
    # -----------------------------------
    commissioned = jcb.datetime_from_conf(chronicle['commissioned'])

    # Check for decommissioned time
    # -----------------------------
    decommissioned = chronicle.get('decommissioned', None)
    if decommissioned:
        decommissioned = jcb.datetime_from_conf(decommissioned)

        # Abort if window_final is after decommissioned
        jcb.abort_if(window_begin >= decommissioned,
                     f"{errors_message_pre} The beginning of the window falls after the "
                     "decommissioned date. This chronicle should not be used after the "
                     "decommissioned date.")

    # Determine if the window spans multiple chronicles, which to adhere to
    chronicle_func = function_map[chronicle['window_option']]

    # List of dictionaries to hold the observing system as it evolves through the chronicles
    # ----------------------------------------------------------------------------
    evolving_observing_system = []

    # Initial list of stations to reject
    # ----------------------------------
    station_reject_list = chronicle.get('stations_to_reject')

    # Store chronicle at the initial commissioned date
    add_to_evolving_observing_system(evolving_observing_system, commissioned, station_reject_list)

    # Get chronicles list
    # -------------------
    chronicles = chronicle.get('chronicles', [])

    # Validation checks on the chronicles
    # -----------------------------------

    # Check chronicles for chronological order and that they are unique
    action_dates = [jcb.datetime_from_conf(chronicle['action_date']) for chronicle in chronicles]
    jcb.abort_if(action_dates != sorted(action_dates),
                 f"{errors_message_pre} The chronicles are not in chronological order.")
    jcb.abort_if(len(action_dates) != len(set(action_dates)),
                 f"{errors_message_pre} The chronicles are not unique. Ensure no two chronicles "
                 "have the same date.")

    # Prepend the action dates with the commissioned date
    action_dates = [commissioned] + action_dates

    # Loop through the chronicles and at each time there will be a complete set of
    # station IDs to reject with the values specified by the chronicle.
    # -------------------------------------------------------------------------------------------
    for chronicle in chronicles:

        # Chronicle action date
        ch_action_date = jcb.datetime_from_conf(chronicle['action_date'])
        ch_action_date_iso = datetime.isoformat(ch_action_date)

        # Update the error message prefix with the action date
        errors_message_pre_ad = "Error processing observation chronicle with action date " + \
                                f"{ch_action_date_iso} for {ob_type}:"

        # If the chronicle has key add_to_reject_list
        if 'add_to_reject_list' in chronicle:
            add_list = chronicle['add_to_reject_list']
            station_reject_list = station_reject_list + add_list

        # If the chronicle has key remove_from_reject_list
        if 'remove_from_reject_list' in chronicle:
            remove_list = chronicle['remove_from_reject_list']
            station_reject_list = [item for item in station_reject_list if item not in remove_list]

        # If the chronicle has key revert_to_previous_chronicle
        if 'revert_to_previous_date_time' in chronicle:
            previous_datetime = jcb.datetime_from_conf(chronicle['revert_to_previous_date_time'])

            # Find the nearest previous datetime in the action_dates list (without going over)
            index_of_previous = get_left_index(errors_message_pre_ad, action_dates,
                                               previous_datetime)

            # Update the channel values to the previous chronicle (using evolving observing system)
            station_reject_list = copy.deepcopy(
                evolving_observing_system[index_of_previous]['station_reject_list'])

        # Add the values after the action to the evolving observing system
        add_to_evolving_observing_system(evolving_observing_system,
                                         ch_action_date, station_reject_list)

    # Now that the entire chronicle has been processed we can return the values to be used for
    # the window. If the window beginning and ending are both between the same action dates then the
    # values will be set to the earlier values. If the window straddles and action date then the
    # values have to be determined using the min/max strategy that the user wishes and has chosen
    # in the variables.

    # Ensure window_begin and window_final are datetime objects
    window_begin = jcb.datetime_from_conf(window_begin)
    window_final = jcb.datetime_from_conf(window_final)

    # Sanity check on the expected input values
    # -----------------------------------------
    jcb.abort_if(window_begin < commissioned,
                 f"{errors_message_pre} The window begin is before the commissioned date.")
    jcb.abort_if(window_final < commissioned,
                 f"{errors_message_pre} The window begin is before the commissioned date.")

    # Abort if the window final is not after window begin
    jcb.abort_if(window_final <= window_begin,
                 f"{errors_message_pre} The window final must be after the window begin.")

    # Find the index of the nearest actions_date that is before or equal to window begin
    index_of_begin = get_left_index(errors_message_pre, action_dates, window_begin)

    # Find the index of the nearest actions_date that is before or equal to window end
    index_of_final = get_left_index(errors_message_pre, action_dates, window_final)

    # Use strategy to determine list for the window
    index_to_use = chronicle_func(index_of_begin, index_of_final)
    final_station_list = \
        copy.deepcopy(evolving_observing_system[index_to_use]['station_reject_list'])

    return final_station_list


# --------------------------------------------------------------------------------------------------
