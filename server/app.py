from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session
)

from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)

import argosdb

from config import CONFIG


APP_SECRET_KEY = 'une_cle_secrete_très_sécurisée'

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

# ----- flask login manager setup ----- #
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"


class ArgosUser(UserMixin):
    def __init__(self, user_id,):
        user_data = argosdb.get_user_by_id(user_id)
      
        if user_data is None:
            self.id = -1
            return
        
        self.id = user_data["id"]
        self.username = user_data["login"]
        self.password_hash = user_data["password"]


@login_manager.user_loader
def load_user(user_id):
    user = ArgosUser(user_id)

    if user.id == -1:
        return None
    return user


# ----- routes ----- #
@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Handle the login process, check user credentials and set session.
    :return: Redirection or Login template
    """
    if current_user is ArgosUser:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if argosdb.check_credentials(username, password):
            user = ArgosUser(argosdb.get_user(username)['id'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return 'Login Failed. Please try again.', 401
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Show the dashboard page to the logged-in user.
    :return: Dashboard template or redirection to login
    """
    return render_template('dashboard.html', username=current_user.username)


@app.route('/logout')
@login_required
def logout():
    """
    Log out the user
    :return: Redirection to login
    """
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    import api  # TODO CHANGE THIS FUCKING THING
    argosdb.init()


    for operator in CONFIG['operators']:
        user_created = argosdb.register_user(operator['username'], operator['password'])
        if user_created:
            print(f"Test user '{operator['username']}' created successfully!")
        else:
            print(f"Test user '{operator['username']}' already exists.")
    
    for listener in CONFIG['listeners']:
        listener_created = argosdb.add_listener(listener['name'], listener['api_key'])
        if listener_created:
            print(f"Test listener created successfully!")
        else:
            print(f"Test listner already exists.")

    app.run(host=CONFIG['server']['host'], port=CONFIG['server']['port'], debug=True)
