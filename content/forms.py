from wtforms import Form, FileField, StringField, TextAreaField
from wtforms.validators import Length


class UploadFiles(Form):
    file = FileField('file')
    name = StringField('name', validators=[Length(min=4, max=128)])
    description = TextAreaField('description')
