import yaml

with open('profile.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

app.run(host=config['server']['host'], port=config['server']['port'])