from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, URLField, FileField
from wtforms.validators import DataRequired, EqualTo, URL, Length, Email
from flask_ckeditor import CKEditorField


class RegForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    email = EmailField(label="Email", validators=[Email()])
    password = PasswordField(label="Password", validators=[
        DataRequired(),
        EqualTo("confirm", message="Passwords must match"),
        Length(min=8, message="Password must be at least 8 characters long")])
    confirm = PasswordField(label="Confirm Password", validators=[DataRequired()])
    submit = SubmitField(label="Register")


class CreatePostForm(FlaskForm):
    title = StringField(label="Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    img_url = URLField(label="Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Blog Content", validators=[DataRequired()])
    submit = SubmitField(label="Submit Post")


class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Let me in", validators=[DataRequired()])


class CommentForm(FlaskForm):
    comment = CKEditorField(label="Leave a Comment", validators=[DataRequired()])
    submit = SubmitField(label="Submit comment")


class UpdateUserInformationForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    email = EmailField(label="Email", validators=[Email()])
    file = FileField(label="Change profile image", validators=[])
    submit_info = SubmitField(label="Submit changes")


class UpdateUserPasswordForm(FlaskForm):
    current_password = PasswordField(label="Password")
    new_password = PasswordField(label="New Password", validators=[
        DataRequired(),
        EqualTo("confirm", message="Passwords must match"),
        Length(min=8, message="Password must be at least 8 characters long")])
    confirm = PasswordField(label="Confirm Password")
    submit_password = SubmitField(label="Change Password")
