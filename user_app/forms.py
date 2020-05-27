from wtforms import Form, StringField, FileField
from wtforms.validators import InputRequired, Length, EqualTo


class Register(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)])
    password = StringField('password', validators=[InputRequired()])
    password2 = StringField('password2', validators=[InputRequired(),
                                                     EqualTo('password', message='Пароли должны совпадать')])
    email = StringField('email', validators=[InputRequired()])
    photo = FileField('photo')


class Auth(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)])
    password = StringField('password', validators=[InputRequired()])
