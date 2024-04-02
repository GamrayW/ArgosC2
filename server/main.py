from flask import Flask, render_template, request, redirect, url_for, session
import db

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_très_sécurisée'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.verify_user(username, password)
        if user:
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            return 'Login Failed. Please try again.', 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.init_db()
    db.create_user("test123","esteban")
    app.run(debug=True)
