import yaml

with open('profile.yaml', 'r') as stream:
    CONFIG = yaml.safe_load(stream)
