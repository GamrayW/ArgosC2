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


# Listener functions are not using the @login_required since listeners
# are not regular users and are identified with their unique api key
@app.route('/api/v1/current_jobs', methods=["GET"])
def current_jobs():
    """
    Retrieve all the jobs that needs to be procceded by the 
    agents.
    :return [dict]: {'id': <int>, 'target_id': int, 'ip_addr': <str>, 'command': <str>}
    """
    api_key = request.headers.get("Authorization")
    listener = argosdb.auth_listener(api_key)

    if listener is None:
        return {'success': False, 'msg': "Bad api key"}
    
    commands = argosdb.get_all_active_commands_for_listener(listener['id'])
    jobs = []
    for command in commands:
        target_info = argosdb.get_target_by_id(command['executed_on'])
        jobs.append({
            'id': command['id'],
            'target_id': target_info['id'],
            'target_name': target_info['display_name'],
            'target_ip': target_info['ip_addr'],
            'command': command['command']
        })

    return jobs


@app.route('/api/v1/heartbeat', methods=["POST"])
def heartbeat():
    """
    Give life signs from agent/listener.
    body params: target_id=<int>
    """
    api_key = request.headers.get("Authorization")
    listener = argosdb.auth_listener(api_key)

    if listener is None:
        return {'success': False, 'msg': "Bad api key"}

    target_id = request.form.get('target_id')
    if target_id is None:
        return {'success': False, 'msg': 'target_id required'}

    argosdb.update_heartbeat_listener(listener['id'])
    argosdb.update_heartbeat_target(target_id)
    return {'success': True, 'msg': "updated heartbeats"}