import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from pathlib import Path
import vyper



class Configuration:
    def __init__(self, configfile=None):
        self.v = vyper.Vyper()
        if configfile:
            self.v.set_config_file(configfile)
        else:
            path = Path(__file__).parent / Path('config')
            self.v.set_config_name('vnf_ipsec')
            self.v.add_config_path(Path.cwd())
            self.v.add_config_path('/etc/vnfipsec')
            self.v.add_config_path(path)
        self.v.read_in_config()


    def __str__(self):
        return yaml.dump(self.v._config, Dumper=Dumper, default_flow_style=False)


    def update_configuration_yaml(self, filepath):
        with open(filepath, "rb") as file:
            yaml_configuration = yaml.load(file, Loader=Loader)
            if yaml_configuration:
                self.configuration.update(yaml_configuration)

    def get(self):
        return self.v

    def get_vnf(self):
        return self.configuration['vnf_ipsec']

    def get_path_prefix(self):
        return Path(self.v.get('vnf_ipsec.path_prefix'))
