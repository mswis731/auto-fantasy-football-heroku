from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    verify = SubmitField("Verify")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Log In")

class TransactionForm(FlaskForm):
    team_id = HiddenField("Team Id", validators=[DataRequired()])
    drop_player = StringField("Drop Player", validators=[DataRequired()])
    add_player = StringField("Add Player", validators=[DataRequired()])
    add = SubmitField("Add")
