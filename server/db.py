import sqlite3

DB_NAME = "users.db"

def execute(query, params=(), fetchone=False):
    """
    Execute a SQL query procedure.
    :param query str: the SQL query, with '?' as parameters like normally.
    :param params tuple opt: the parameters as an iterable like normally.
    :param fetchone bool: whether to fetch one or all results.
    :return list or dict: The response from the db (if there's one).
    """
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    response = cursor.execute(query, params)
    response = response.fetchone() if fetchone else response.fetchall()

    connection.commit()
    connection.close()

    return response

def init_db():
    create_users_table = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    '''
    execute(create_users_table)

def create_user(username, password):
    query = "INSERT INTO users (username, password) VALUES (?, ?)"
    execute(query, (username, password))


def verify_user(username, password):
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    user = execute(query, (username, password), fetchone=True)
    return user
