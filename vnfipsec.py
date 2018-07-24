#!/usr/env/python3
import configuration
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import jinja2

def config_path(config, path):
    return (config.get_path_prefix() / Path(path)).as_posix()


def template_charon(env, config):
    template = env.get_template('charon.conf.jinja2')
    template.stream(vti=config.v.get_bool('vti')).dump(config_path(config, 'strongswan.d/charon.conf'))


def template_farp(env, config):
    template = env.get_template('farp.conf.jinja2')
    template.stream(load_module=config.v.get_bool('vti')).dump(config_path(config, 'strongswan.d/charon/farp.conf'))


if __name__ == '__main__':
    config = configuration.Configuration()
    # default_config = "config/defaults.yaml"
    # config.update_configuration_yaml(Path(default_config))
    print(config)

    env = Environment(
        loader=PackageLoader('vnfipsec', 'templates'),
        # loader=FileSystemLoader('./templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template_charon(env, config)
    template_farp(env, config)

