from wtforms import Form, StringField
from wtforms.validators import InputRequired, Length
from wtforms.widgets import Input, PasswordInput


class Register(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)], widget=Input)


class Auth(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)], widget=Input)
    password = StringField('password', validators=[InputRequired()], widget=PasswordInput)
