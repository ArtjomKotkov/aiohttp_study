from wtforms import Form, TextAreaField


class Chat(Form):
    text = TextAreaField('text')
