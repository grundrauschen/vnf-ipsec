import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class Configuration:
    def __init__(self):
        self.configuration = {}

    def __str__(self):
        return yaml.dump(self.configuration, Dumper=Dumper, default_flow_style=False)


    def update_configuration_yaml(self, filepath):
        with open(filepath, "rb") as file:
            yaml_configuration = yaml.load(file, Loader=Loader)
            if yaml_configuration:
                self.configuration.update(yaml_configuration)
