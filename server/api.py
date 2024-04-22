if __name__ == "__main__":
    raise Exception("This should not be run as a standalone")

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
    Get all the commands typed by the current user on a target
    :param target_id int: the id of the target
    :return [dict]: the commands info
    """
    commands = argosdb.get_user_command_history_of_target(target_id, current_user.id)
    if commands == None:
        return [{'err': True, 'msg': "No command on this target"}]
    return commands


@app.route('/api/v1/targets', methods=["GET"])
@login_required
def targets():
    """
    Return the list of existing targets
    :return [dict]: the list of targets (see db schema for dict structure)
    """
    targets = argosdb.get_all_targets()
    return targets


@app.route('/api/v1/send_command/<target_id>', methods=["POST"])
@login_required
def send_command(target_id=-1):
    """
    Send a new command to a target
    post body should be: 'cmd'=<data>
    :return str: ko/ok if it succeeded
    """
    command = request.form.get('cmd')
    if command is None:
        return "ko"
    
    if argosdb.get_target_by_id(target_id) is None:
        return "ko"
    argosdb.add_new_command(command, target_id, current_user.id)
    return "ok"