#!/usr/env/python3
import configuration
from pathlib import Path

if __name__ == '__main__':
    config = configuration.Configuration()
    default_config = "config/defaults.yaml"
    config.update_configuration_yaml(Path(default_config))
    print(config)
