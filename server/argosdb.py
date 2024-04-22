import psycopg
import hashlib
from datetime import datetime


# change this to go in config.py
HOST    = ["127.0.0.1", 5432]
DB_NAME = "argos_db"
DB_USER = "argos"
DB_PASS = "changeme"

# initiate connection with the db at the start
connection = psycopg.connect(f"postgresql://{DB_USER}:{DB_PASS}@{HOST[0]}:{HOST[1]}/{DB_NAME}")
cursor = connection.cursor()

# ----- ERRORS ----- #
class UserAlreadyExists(Exception):
    pass


# ----- FUNCTIONS ----- #
def create_tables():
    """
    Initialise the database with all our custom tables.
    There's users, targets and commands.
    """
    connection.execute("""\
    CREATE TABLE Users (
        id SERIAL PRIMARY KEY,
        login VARCHAR,
        password VARCHAR
    );""")

    connection.execute("""\
    CREATE TABLE Listeners (
        id SERIAL PRIMARY KEY,
        name VARCHAR,
        heartbeat INTEGER,
        api_key VARCHAR
    );""")

    connection.execute("""\
    CREATE TABLE Targets (
        id SERIAL PRIMARY KEY,
        listener INTEGER,
        display_name VARCHAR,
        ip_addr VARCHAR,
        heartbeat INTEGER,
        last_command INTEGER
    );""")

    connection.execute("""\
    CREATE TABLE Commands (
        id SERIAL PRIMARY KEY,
        owner INTEGER,
        executed_on INTEGER,
        completed BOOL,
        command VARCHAR,
        response VARCHAR,
        executed_at INTEGER
    );""")

    connection.commit()


# Utils funcs
def parse_user(user_data):
    return {
        "id": user_data[0],
        "login": user_data[1],
        "password": user_data[2]
    }


def parse_listener(listener_data):
    return {
        'id': listener_data[0],
        'name': listener_data[1],
        'heartbeat': listener_data[2],
        # we don't provide the api-key
    }


def parse_targets(target_data):
    return {
        'id': target_data[0],
        'listener': target_data[1],
        'display_name': target_data[2],
        'ip_addr': target_data[3],
        'heartbeat': target_data[4],
        'last_command_id': target_data[5]
    }


def parse_command(command_data):
    return {
        'id': command_data[0],
        'owner': command_data[1],
        'executed_on': command_data[2],
        'completed': command_data[3],
        'command': command_data[4],
        'response': command_data[5],
        'executed_at': command_data[6],
    }


def get_tables():
    """
    Get all custom tables in the db
    :return list: The list of table names or None if there's none
    """
    tables = connection.execute("SELECT table_name FROM information_schema.tables \
                         WHERE table_schema='public' AND table_type='BASE TABLE';").fetchall()
    return list(map(lambda el: el[0], tables))


def init():
    """
    Init the db
    Check if there's some tables, and if not creates them
    """
    if get_tables() == []:
        print("Creating tables...")
        create_tables()


# User functions
def get_user(login):
    """
    Retrieve a user from it's login
    :param login str: the login, no shit
    """
    user = connection.execute("SELECT * FROM Users WHERE login=%s;", (login,)).fetchone()
    if user is None:
        return None

    return parse_user(user)


def get_user_by_id(user_id):
    """
    Retrieve a user from it's id
    :param id int: the id
    """
    user = connection.execute("SELECT * FROM Users WHERE id=%s;", (user_id,)).fetchone()
    if user is None:
        return None

    return parse_user(user)


def register_user(login, password):
    """
    register a new user. Checks if the login already exists
    before.
    :login str: unique identifier
    :password str: clear-text password of the new user
    :return bool: if the user is registred (False = user already regisered)
    """
    password = hashlib.sha512(password.encode()).hexdigest()
    user = get_user(login)
    if user is not None:
        return False

    connection.execute("INSERT INTO Users(login, password) VALUES (%s, %s);", (login, password))
    connection.commit()
    return True


def check_credentials(login, password):
    """
    Validate a login:password
    :param login str: the login
    :param password str: the cleartext password
    :return bool: if the credentials matches or not
    """
    password = hashlib.sha512(password.encode()).hexdigest()

    user = get_user(login)
    if user is None:
        return False
    return password == user['password']


# Listeners functions
def get_listener(name):
    """
    Get the listener id from the specified name
    :param name str: the name of the listener
    """
    listener = connection.execute("SELECT id FROM Listeners WHERE name=%s;", (name,)).fetchone()
    if listener is None:
        return None
    return listener[0]


def auth_listener(api_key):
    """
    Check if the provided api_key is from a listener, and
    returns it if so.
    :param api_key str: the api key provided
    :return dict: the listener dict object (see db schema)
    """
    api_key_hash = hashlib.sha512(api_key.encode()).hexdigest()

    listener = connection.execute("SELECT * FROM Listeners WHERE api_key = %s", (api_key_hash,)).fetchone()
    if listener is None:
        return None
    return parse_listener(listener)


def add_listener(name, api_key):
    """
    Add a new listener to the database.
    :param name str: the unique name used to identify the listener
    :param api_key str: the clear text api key used to authentificate the listener
    """
    api_key_hash = hashlib.sha512(api_key.encode()).hexdigest()
    user = get_listener(name)
    if user is not None:
        return False

    connection.execute("INSERT INTO Listeners(name, api_key) VALUES (%s, %s);", (name, api_key_hash))
    connection.commit()
    return True


def update_heartbeat_listener(listener_id):
    """
    Change the heartbeat timestamp of the listener to current time
    :param listener_id int: the id of the listener
    """
    timestamp = int(datetime.now().timestamp())

    connection.execute("UPDATE Listeners SET heartbeat = %s WHERE id = %s", (timestamp, listener_id))
    connection.commit()


# Targets functions
def get_all_targets():
    """
    Retrieve all the targets
    :return [dict]: the list of target dict object (see db schema)
    """
    targets = connection.execute("SELECT * FROM Targets").fetchall()
    result = []
    for target in targets:
        result.append(parse_targets(target))
    
    return result


def get_target_by_id(target_id):
    """
    Retrieve a target from it's id
    :param target_id int: the id of the target
    :return dict: the target dict object (see db schema)
    """
    target = connection.execute("SELECT * FROM Targets WHERE id=%s;", (target_id,)).fetchone()
    if target is None:
        return None

    return parse_targets(target)


def get_target_by_name(name):
    """
    Retrieve a target from it's display name
    :param name: the unique display name
    :return dict: the target dict object (see db schema)
    """
    target = connection.execute("SELECT * FROM Targets WHERE display_name=%s;", (name,)).fetchone()
    if target is None:
        return None

    return parse_targets(target)


def get_targets_by_ip(ip_addr):
    """
    Retrieve the target(s) using the ip
    :param ip_addr str: the ip used
    :return [dict]: the list of targets using it
    """
    targets = connection.execute("SELECT * FROM Targets WHERE ip_addr=%s;", (ip_addr,)).fetchall()
    if targets is None:
        return None

    result = []
    for target in targets: 
        result.append(parse_targets(target))
    return result


def add_new_target(display_name, ip_addr, listener_id):
    """
    Add a new target, checks for display name uniqueness
    :param display_name str: the unique display name to identify the target 
    :param ip_addr str: the ip address of the target
    :param listener_id str: the id of the lister that owns this target
    :return bool: false if there's already a target using display name, true if success
    """
    if get_target_by_name(display_name) is not None:
        return False

    timestamp = int(datetime.now().timestamp())

    connection.execute("INSERT INTO Targets(listener, display_name, ip_addr, heartbeat) \
                       VALUES (%s, %s, %s, %s);", (listener_id, display_name, ip_addr, timestamp))
    connection.commit()
    return True


def update_heartbeat_target(target_id):
    """
    Change the heartbeat timestamp of the target to current time
    :param target_id int: the id of the target
    """
    timestamp = int(datetime.now().timestamp())

    connection.execute("UPDATE Targets SET heartbeat = %s WHERE id = %s", (timestamp, target_id))
    connection.commit()


# Commands function
def get_user_last_command_on_target(target_id, user_id):
    """
    Get the last command the specified user sent to the target
    :param target_id int: id of target
    :param user_id int: id of user
    :return dict: the command dict object (see db schema)
    """
    last_command = connection.execute("SELECT * FROM Commands WHERE executed_on = %s\
                                   AND owner = %s;", (target_id, user_id)).fetchone()
    if last_command == None:
        return None

    return parse_command(last_command)


def get_user_command_history_of_target(target_id, user_id):
    """
    Get the history of a user commands on target
    :param target_id int: the id of the target
    :param user_id int: the id of the user
    :return [dict]: the list of command dict object (see db schema)
    """
    commands = connection.execute("SELECT * FROM Commands WHERE executed_on = %s\
                                   AND owner = %s ORDER BY executed_at ASC;", (target_id, user_id)).fetchall()

    result = []
    for command in commands: 
        result.append(parse_command(command))
    return result


def get_all_active_commands_for_listener(listener_id):
    """
    Get all active commands for a specified listener, regardless of the target
    :param listener_id int: the id of the listener
    """
    commands = connection.execute("SELECT c.* FROM Commands c \
                                   JOIN Targets t\
                                   ON c.executed_on = t.id \
                                   AND NOT c.completed;",).fetchall()
    result = []
    for command in commands: 
        result.append(parse_command(command))
    return result


def add_new_command(command, target_id, user_id):
    """
    Create a new command linked with User and Target.
    :param command str: the command itself
    :param target_id int: the id of the target
    :param user_id int: the id of the user
    """
    timestamp = int(datetime.now().timestamp())

    connection.execute("""\
        INSERT INTO Commands(owner, executed_on, completed, command, executed_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, target_id, False, command, timestamp))

    connection.commit()


if __name__ == "__main__":
    print("----------Wiping db-----------")
    connection.execute("DROP TABLE IF EXISTS Users")
    connection.execute("DROP TABLE IF EXISTS Listeners")
    connection.execute("DROP TABLE IF EXISTS Targets")
    connection.execute("DROP TABLE IF EXISTS Commands")
    connection.commit()

    print("----------Init DB-----------")
    print(f"Current tables: {get_tables()}")
    print("Calling init...")
    init()
    print(f"Current tables: {get_tables()}")
    
    print("----------Testing Users-----------")
    if not register_user("John", "12345"):
        print("User John already registered")

    print(get_user("John"))
    print(connection.execute("SELECT * FROM Users;").fetchall())

    print("----------Testing Targets-----------")
    if not add_new_target("test_device", "127.0.0.1", 1):
        print("test_device already registered")

    print(get_target_by_name("test_device"))
    print(get_targets_by_ip("127.0.0.1"))
    print(connection.execute("SELECT * FROM Targets").fetchall())

    print("----------Testing Commands-----------")
    add_new_command("ls /", 1, 1)
    print(connection.execute("SELECT * FROM Commands").fetchall())
    print(get_user_last_command_on_target(1, 1))

    print("----------Wiping db-----------")
    connection.execute("DROP TABLE IF EXISTS Users")
    connection.execute("DROP TABLE IF EXISTS Listeners")
    connection.execute("DROP TABLE IF EXISTS Targets")
    connection.execute("DROP TABLE IF EXISTS Commands")
    connection.commit()