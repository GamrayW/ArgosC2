from flask import Flask, render_template, request, redirect, url_for, session
import argosdb


APP_SECRET_KEY = 'une_cle_secrete_très_sécurisée'


app = Flask(__name__)
app.secret_key = APP_SECRET_KEY


@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Handle the login process, check user credentials and set session.

    :return: Redirection or Login template
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if argosdb.check_credentials(username, password):
            user = argosdb.get_user(username)
            session['username'] = user['login']
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return 'Login Failed. Please try again.', 401
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    """
    Show the dashboard page to the logged-in user.

    :return: Dashboard template or redirection to login
    """
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])


@app.route('/logout')
def logout():
    """
    Log out the user by clearing the session.

    :return: Redirection to login
    """
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    argosdb.init()

    test_username = "testuser"
    test_password = "password123"
    user_created = argosdb.register_user(test_username, test_password)
    if user_created:
        print(f"Test user '{test_username}' created successfully!")
    else:
        print(f"Test user '{test_username}' already exists.")

    app.run(debug=True)
