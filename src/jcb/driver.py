# --------------------------------------------------------------------------------------------------

import click
import jcb
import sys
import yaml

# --------------------------------------------------------------------------------------------------


@click.group()
@click.version_option(version=jcb.version(), prog_name="Jedi Configuration Builder (jcb)")
def jcb_driver():
    """
    Welcome to the Jedi Configuration Builder (jcb).

    This is the top level driver for the Jedi Configuration Builder. There are two main APIs for
    jcb. Where the rendering is called in memory, for example from a workflow system. And where the
    rendering is called offline, reading templates from one YAML and writing out a new YAML that can
    be passed to the JEDI executable.

      import jcb
      jedi_dict = jcb.render(dictionary_of_templates)

      or

      jcb render dictionary_of_templates.yaml jedi_dict.yaml

    """
    pass


# --------------------------------------------------------------------------------------------------


@jcb_driver.command()
@click.argument('dictionary_of_templates')
@click.argument('jedi_yaml')
def render(dictionary_of_templates, jedi_yaml):

    """
    Create a new YAML file for driving a JEDI experiment using a dictionary of templates.

    Arguments: \n
        dictionary_of_templates (str): Path to a YAML containing the dictionary of templates. \n
        jedi_yaml (str): YAML output file containing JEDI configuration. \n
    """

    # Open the dictionary of templates yaml into a dictionary
    with open(dictionary_of_templates, 'r') as f:
        dictionary_of_templates = yaml.safe_load(f)

    # Call the jcb render function
    try:
        jedi_dict = jcb.render(dictionary_of_templates)
    except Exception as e:
        message = f"JCB failed to render the dictionary of templates | {e}"
        raise click.ClickException(message)

    # Write jedi_dict to yaml file
    with open(jedi_yaml, 'w') as f:
        yaml.dump(jedi_dict, f, default_flow_style=False, sort_keys=False)


# --------------------------------------------------------------------------------------------------


def main():
    """
    Main entry point for jcb.
    """
    jcb_driver()


# --------------------------------------------------------------------------------------------------
