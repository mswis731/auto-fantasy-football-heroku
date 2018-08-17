from app import app, db
from flask import request, render_template, url_for, redirect, jsonify
from forms import LoginForm, SignupForm
from models import User
from tasks import verify_user_task

@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()

        if user == None or password != User.decrypt_password(user.password):
            form.username.errors.append("Incorrect username or password")
        else:
            return redirect(url_for("wip"))

    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            form.username.errors.append("User with that username already exists")
        else:
            user = User(username, password)
            db.session.add(user)
            db.session.commit()

            return redirect(url_for("wip"))

    return render_template("signup.html", form=form)

@app.route("/verify-user", methods=["POST"])
def verify_user():
    form = SignupForm(request.form)
    username = form.username.data
    password = form.password.data

    task = verify_user_task.delay(username, password)
    return jsonify({}), 202, { 'location': url_for('task_status',
                                                   task_id=task.id) }


@app.route('/task-status/<task_id>')
def task_status(task_id):
    task = verify_user_task.AsyncResult(task_id)
    response = {
        "state" : task.state,
        "status" : str(task.info)
    }
    return jsonify(response)

@app.route("/wip")
def wip():
    return "Hello World!"
