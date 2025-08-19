# JEDI Configuration Builder

### Repository status:

[![JCB Tests](https://github.com/NOAA-EMC/jcb/actions/workflows/basic_testing.yaml/badge.svg?branch=develop)](https://github.com/NOAA-EMC/jcb/actions/workflows/basic_testing.yaml)

### Installation

For the latest development version from PyPI (published automatically on pushes to develop):

``` shell
pip install jcb
```

For development or to install from source:

``` shell
git clone https://github.com/noaa-emc/jcb
cd jcb

# Optional step if you want to run the client integration tests
./jcb_client_init.py  # May first require `pip install pyyaml` if it is not available

pip install --prefix=/path/to/where/you/want/installed .

# Run the tests
pytest
```

### Description

How to use from the command line:

``` shell
jcb render dictionary_of_templates.yaml jedi_config.yaml
```

The below shows two examples of calling jcb from a python client. In each case you have to provide a dictionary that describes all the ways that you want to render the templates in the contained JEDI YAML files.

First jcb provides a convenient single line call passing in the dictionary of templated and getting back the dictionary. The dictionary of templates has to contain an `algorithm` key telling the system which JEDI algorithm you want to run.

``` python
import jcb

jedi_config_dict = jcb.render(dictionary_of_templates)
```

For situations where you wish to create YAML files for several algorithms using the same dictionary of templates you can access the class directly.

``` python
import jcb

jcb_obj = jcb.Renderer(dictionary_of_templates)
jedi_dict_2_a = jcb_obj.render('hofx4d')
jedi_dict_2_b = jcb_obj.render('variational')
```


