#!/usr/bin/env python


# --------------------------------------------------------------------------------------------------


import os
import subprocess
import typing

import yaml


# --------------------------------------------------------------------------------------------------


bold = '\033[1m'
red = '\033[91m'
green = '\033[92m'
end = '\033[0m'


# --------------------------------------------------------------------------------------------------


def write_message(message: str, center: bool = False) -> None:

    """Write a message, optionally centered, and print it line by line.

    Args:
        message (str): The message to be written and printed.
        center (bool): If True, center each line of the message. Defaults to False.
    """

    # Max line length
    max_line_length = 100

    # Break the message into a list of lines max 100 characters but do not cut a word in half
    lines = []
    while len(message) > max_line_length:
        last_space = message[:max_line_length].rfind(' ')
        lines.append(message[:last_space])
        message = message[last_space+1:]
    lines.append(message)

    # If center is true center the lines
    if center:
        lines = [line.center(max_line_length) for line in lines]

    # Remove any lines that are empty
    lines = [line for line in lines if line != '']

    # Print the lines
    for line in lines:
        print(line)


# --------------------------------------------------------------------------------------------------


def get_jcb_branch() -> typing.Optional[str]:

    """Get the current Git branch name.

    Executes a Git command to retrieve the current branch name.
    Returns the branch name unless it is 'HEAD' or 'develop',
    in which case it returns None.

    Returns:
        Optional[str]: The current Git branch name, or None if the branch
        is 'HEAD', 'develop', or if an error occurs.
    """

    # Command to get git branch
    git_branch_command = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']

    # Return current branch
    try:
        branch = subprocess.check_output(git_branch_command).strip().decode('utf-8')
        return branch if branch != 'HEAD' and branch != 'develop' else None
    except subprocess.CalledProcessError:
        return None


# --------------------------------------------------------------------------------------------------


def branch_exists_on_remote(git_ls_remote_command: typing.List[str]) -> bool:

    """Check if a branch exists on the remote repository.

    Executes a Git command to check for the existence of a branch
    on the remote repository.

    Args:
        git_ls_remote_command (List[str]): The Git command to list remote branches.

    Returns:
        bool: True if the branch exists on the remote repository, False otherwise.
    """

    # Return status of branch existence
    try:
        output = subprocess.check_output(git_ls_remote_command)
        return bool(output)
    except subprocess.CalledProcessError:
        return False


# --------------------------------------------------------------------------------------------------


def update_default_refs(jcb_apps: typing.Dict[str, typing.Dict[str, typing.Any]]) -> None:

    """Update the default Git references for jcb apps based on the current branch.

    Gets the current branch of the jcb repo and updates the default branch
    for each app in jcb_apps if the branch exists on the remote.

    Args:
        jcb_apps (Dict[str, Dict[str, Any]]): A dictionary containing app configurations,
        where the key is the app name and the value is a dictionary with configuration details.

    Returns:
        None
    """

    # Get the current branch of the jcb repo
    jcb_branch = get_jcb_branch()

    # Nothing to do unless there is a branch  called something other than develop
    if jcb_branch is None:
        return

    # Write message
    write_message(f'The branch for jcb is {red + jcb_branch + end}. Looking for this branch '
                  'for the clients.')

    # Loop over jcb_apps and update default branch
    for app, app_conf in jcb_apps.items():

        # Check if the default branch exists
        full_url = f'https://github.com/{app_conf["git_url"]}.git'
        git_ls_remote_command = ['git', 'ls-remote', '--heads', full_url, jcb_branch]

        # If the branch exists, update the default branch
        found = red + 'not found' + end
        if branch_exists_on_remote(git_ls_remote_command):
            found = green + 'found' + end
            app_conf['git_ref'] = jcb_branch
        write_message(f'  Branch {jcb_branch} {found} for {app}')
    write_message(' ')


# --------------------------------------------------------------------------------------------------


def clone_or_update_repos(jcb_apps: typing.Dict[str, typing.Dict[str, typing.Any]]) -> None:

    """Clone or update repositories based on the provided configuration.

    Loops over jcb_apps and clones the repositories if the target path does not exist.
    If the repository already exists at the target path, it prints a warning message.

    Args:
        jcb_apps (Dict[str, Dict[str, Any]]): A dictionary containing app configurations,
        where the key is the app name and the value is a dictionary with configuration details.

    Returns:
        None
    """

    # Loop over jcb_apps and clone or update the repositories
    for app, app_conf in jcb_apps.items():

        target_path = app_conf['target_path']

        # Check if the target path exists
        if not os.path.exists(target_path):

            # Clone command
            full_url = f'https://github.com/{app_conf["git_url"]}.git'
            git_clone = ['git', 'clone', full_url, '-b', app_conf['git_ref'],
                         target_path]

            # Clone the repository
            command_string = ' '.join(git_clone)
            write_message(f'Cloning {app} with command: {command_string}')
            subprocess.run(git_clone, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        else:

            # Print warning that repo is already cloned
            write_message(f'Repository {app} already cloned at {target_path}. Update '
                          'manually or remove to clone again using this script.')

        write_message(' ')


# --------------------------------------------------------------------------------------------------


if __name__ == "__main__":

    # Write initial message
    write_message(' ')
    write_message('-'*100)
    write_message(' ')
    write_message(bold + 'Running jcb client initialization script' + end, True)
    write_message(' ')
    write_message('This script will clone any of the jcb clients that are registered in '
                  'jcb_apps.yaml.\n')

    # Get the path of this file
    file_path = os.path.dirname(os.path.realpath(__file__))

    # Open the jcb_apps.yaml file
    with open(os.path.join(file_path, 'jcb_clients.yaml')) as file:
        jcb_apps = yaml.load(file, Loader=yaml.FullLoader)

    # Required keys
    required_keys = ['git_url', 'git_ref']

    # Set the path to where the applications will be cloned
    jcb_config_path = os.path.join(file_path, 'src', 'jcb', 'configuration')

    # Loop over jcb_apps and make sure required keys are present and add target_path
    for app, app_conf in jcb_apps.items():
        for key in required_keys:
            if key not in app_conf:
                raise Exception(f'Key \'{key}\' not found in jcb_apps.yaml')
        app_conf['target_path'] = os.path.join(jcb_config_path, 'apps', app)

    # Add jcb-algorithms to the dictionary
    jcb_apps['algorithms'] = {
        'git_url': 'noaa-emc/jcb-algorithms',
        'git_ref': 'develop',
        'target_path': os.path.join(jcb_config_path, 'algorithms')
    }

    # Update the default refs for the clients
    update_default_refs(jcb_apps)

    # Clone or update the repositories
    clone_or_update_repos(jcb_apps)

    # Link all the application test YAML files to client_integration test directory
    for app, app_conf in jcb_apps.items():
        test_path = os.path.join(app_conf['target_path'], 'test', 'client_integration')
        if not os.path.exists(test_path):
            continue
        yaml_files = [f for f in os.listdir(test_path) if f.endswith('.yaml')]
        # Link all the files (may already exist)
        for yaml_file in yaml_files:
            src = os.path.join(test_path, yaml_file)
            dst = os.path.join(file_path, 'test', 'client_integration', yaml_file)
            if os.path.exists(dst):
                os.remove(dst)
            os.symlink(src, dst)

    write_message('Initialization of jcb clients is complete')
    write_message(' ')
    write_message('-'*100)


# --------------------------------------------------------------------------------------------------
