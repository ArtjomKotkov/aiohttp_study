from wtforms import Form, StringField
from wtforms.validators import InputRequired, Length, EqualTo


class Register(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)])
    password = StringField('password', validators=[InputRequired()])
    password2 = StringField('password2', validators=[InputRequired(),
                                                     EqualTo('password', message='Пароли должны совпадать')])


class Auth(Form):
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=30)])
    password = StringField('password', validators=[InputRequired()])
