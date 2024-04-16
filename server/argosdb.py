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
    CREATE TABLE Targets (
        id SERIAL PRIMARY KEY,
        display_name VARCHAR,
        ip_addr VARCHAR,
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
    :param login: the login, no shit
    """
    user = connection.execute("SELECT * FROM Users WHERE login=%s;", (login,)).fetchone()
    if user is None:
        return None

    return {
        "id": user[0],
        "login": user[1],
        "password": user[2]
    }


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


# Targets functions
def get_target_by_name(name):
    """
    Retrieve a target from it's display name
    :param name: the unique display name
    :return dict: the target dict object (see db schema)
    """
    target = connection.execute("SELECT * FROM Targets WHERE display_name=%s;", (name,)).fetchone()
    if target is None:
        return None

    return {
        "id": target[0],
        "display_name": target[1],
        "ip_addr": target[2],
        "last_command_id": target[3]
    }


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
        result.append({
                "id": target[0],
                "display_name": target[1],
                "ip_addr": target[2],
                "last_command_id": target[3]
            })
    return result


def add_new_target(display_name, ip_addr):
    """
    Add a new target, checks for display name uniqueness
    :param display_name str: the unique display name to identify the target 
    :param ip_addr str: the ip address of the target
    :return bool: false if there's already a target using display name, true if success
    """
    if get_target_by_name(display_name) is not None:
        return False

    connection.execute("INSERT INTO Targets(display_name, ip_addr) VALUES (%s, %s);", (display_name, ip_addr))
    connection.commit()
    return True


# Commands function
def get_command_history_of_target(display_name):
    """
    Get the history of commands of a target
    :param display_name str: the name of the target
    :return [dict]: the list of command dict object (see db schema)
    """
    target_id = get_target_by_name(display_name)["id"]

    commands = connection.execute("SELECT * FROM Commands WHERE executed_on = %s\
                                   ORDER BY executed_at ASC;", (target_id,)).fetchall()

    return commands


def add_new_command(command, target_name, user_name):
    """
    Create a new command linked with User and Target.
    :param command str: the command itself
    :param target_name str: the display_name of the Target
    :param user_name str: the login of the User
    """
    user_id = get_user(user_name)["id"]
    target_id = get_target_by_name(target_name)["id"]

    timestamp = int(datetime.now().timestamp())

    connection.execute("""\
        INSERT INTO Commands(owner, executed_on, completed, command, executed_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, target_id, False, command, timestamp))

    connection.commit()


if __name__ == "__main__":
    print("----------Whiping db-----------")
    connection.execute("DROP TABLE IF EXISTS Users")
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
    if not add_new_target("test_device", "127.0.0.1"):
        print("test_device already registered")

    print(get_target_by_name("test_device"))
    print(get_targets_by_ip("127.0.0.1"))
    print(connection.execute("SELECT * FROM Targets").fetchall())

    print("----------Testing Commands-----------")
    add_new_command("ls /", "test_device", "John")
    print(connection.execute("SELECT * FROM Commands").fetchall())
    print(get_command_history_of_target("test_device"))