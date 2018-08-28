from app import app, db, login_manager
from flask import request, render_template, url_for, redirect, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from forms import LoginForm, SignupForm, TransactionForm
from models import User, Team, Transaction
from tasks import verify_user_task

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    else:
        return redirect(url_for("list_transactions"))

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
            login_user(user)
            return redirect(url_for("list_transactions"))

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

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

            login_user(user)
            return redirect(url_for("list_transactions"))

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

@app.route('/transactions/<team_id>')
def transactions(team_id):
    def transaction_info(transaction):
        return {
            "id": transaction.id,
            "drop_player": transaction.drop_player,
            "add_player": transaction.add_player,
            "status": transaction.status.value
        }

    transactions = Team.query.get(team_id).transactions
    response = [ transaction_info(transaction) for transaction in transactions ]
    return jsonify(response)

@app.route("/add-transaction", methods=["POST"])
def add_transaction():
    form = TransactionForm(request.form)
    team_id = form.team_id.data
    drop_player = form.drop_player.data
    add_player = form.add_player.data

    if form.validate():
        transaction = Transaction(
            drop_player=drop_player,
            add_player=add_player,
            team_id=team_id,
            status=Transaction.Status.PENDING
        )
        db.session.add(transaction)
        db.session.commit()
        return jsonify({}), 200, {}
    return jsonify({}), 404, {}

@app.route("/remove-transaction/<transaction_id>", methods=["POST"])
def remove_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({}), 200, {}

@app.route("/transactions")
@login_required
def list_transactions():
    form = TransactionForm(request.form)
    return render_template("transactions.html", form=form)
