from flask import Flask, render_template, request, flash, redirect, url_for, abort
from forms import RegForm, CreatePostForm, LoginForm, CommentForm, UpdateUserInformationForm, UpdateUserPasswordForm
from flask_bootstrap import Bootstrap4
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from models import db, User, BlogPost, Comment, CommentReplies
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from mail import sent_email
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Bootstrap
bootstrap = Bootstrap4(app)
app.secret_key = os.getenv("APP_SECRET_KEY")

# Initialize CKEditor
ckeditor = CKEditor(app)

# Initialize Flask Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# DB configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
db.init_app(app)

# File upload configuration
UPLOAD_FOLDER = f'static/assets/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Create database tables if they don't exist
with app.app_context():
    db.create_all()


# Decorator to check user roles for specific routes
def role_required(roles):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.can(roles):
                abort(403, "You don't have the required permissions")
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def determine_user_role():
    # Check the user count, if first user make Admin
    return "admin" if User.query.count() == 0 else "reader"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Load user from the database
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}


@app.route("/")
def index():
    all_posts = BlogPost.query.all()
    return render_template("index.html", all_posts=all_posts)


@app.route("/about")
def about():
    return render_template("about.html")


# Route to handle contact form submissions
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        name = data["name"]
        email = data["email"]
        phone = data["pnumber"]
        message = data["message"]
        sent_email(name, email, phone, message)
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered! Try Login")
            return redirect(url_for("login"))
        elif User.query.filter_by(username=form.username.data).first():
            flash("Username taken")
            return render_template("register.html", form=form)
        else:
            user_role = determine_user_role()
            # Create a new user and add to the database
            new_user = User(username=form.username.data,
                            email=form.email.data.lower(),
                            password=generate_password_hash(form.password.data, salt_length=8),
                            roles=user_role)
            db.session.add(new_user)
            db.session.commit()
            # Log in the new user
            login_user(new_user)
            return redirect(url_for("index"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            if check_password_hash(pwhash=user.password, password=form.password.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Wrong Password")
                return redirect(url_for("login"))
        else:
            flash("Email Doesnt Exist! Please Register")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/post/<post_title>", methods=["GET", "POST"])
def show_post(post_title):
    form = CommentForm()
    post_to_read = BlogPost.query.filter_by(title=post_title).first()
    comments = Comment.query.all()
    comment_replies = CommentReplies.query.all()
    if form.validate_on_submit():
        # Create a new comment and add to the database
        new_comment = Comment(comment_text=form.comment.data,
                              post_id=post_to_read.id,
                              commenter=current_user.id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_title=post_title))

    return render_template("post.html", post=post_to_read, comments=comments,
                           comment_replies=comment_replies, form=form)


@app.route("/add-reply/<post_title>/<int:comment_id>", methods=["GET", "POST"])
@login_required
def add_reply(post_title, comment_id):
    post = BlogPost.query.filter_by(title=post_title).first()
    comment = Comment.query.filter_by(id=comment_id).first()
    form = CommentForm()
    if form.validate_on_submit():
        # Create a new reply and add to the database
        new_reply = CommentReplies(reply_text=form.comment.data,
                                   comment_id=comment_id,
                                   user_id=current_user.id)
        db.session.add(new_reply)
        db.session.commit()
        return redirect(url_for("show_post", post_title=post_title))
    return render_template("reply.html", form=form, post=post, comment=comment)


@app.route("/create-post", methods=["GET", "POST"])
@role_required(["admin"])
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        # Create a post and add to database
        new_post = BlogPost(title=form.title.data,
                            subtitle=form.subtitle.data,
                            img_url=form.img_url.data,
                            body=form.body.data,
                            user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("create-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@role_required(["admin"])
def edit_post(post_id):
    post_to_edit = BlogPost.query.filter_by(id=post_id).first()
    form = CreatePostForm(title=post_to_edit.title,
                          subtitle=post_to_edit.subtitle,
                          img_url=post_to_edit.img_url,
                          body=post_to_edit.body,
                          user_id=current_user)
    if form.validate_on_submit():
        # Submit the changes to the post in the database
        post_to_edit.title = form.title.data
        post_to_edit.subtitle = form.subtitle.data
        post_to_edit.img_url = form.img_url.data
        post_to_edit.body = form.body.data
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("create-post.html", form=form)


@app.route("/edit-comment/<post_title>/<content_type>/<int:comment_id>", methods=["POST", "GET"])
def edit_comment(post_title, comment_id, content_type):

    # check if the user have permission to edit
    if (current_user.roles not in ["admin", "moderator"]
            and current_user.id != Comment.query.filter_by(id=comment_id).first().user.id):
        return abort(403, "You don't have the required permissions")

    # check the content type - comment or reply and get it from the database
    if content_type == "comment":
        comment_to_edit = Comment.query.filter_by(id=comment_id).first()
        form = CommentForm(comment=comment_to_edit.comment_text)
    elif content_type == "reply":
        comment_to_edit = CommentReplies.query.filter_by(id=comment_id).first()
        form = CommentForm(comment=comment_to_edit.reply_text)
    else:
        return abort(404)

    # Update the data in the database
    if form.validate_on_submit():
        if content_type == "comment":
            comment_to_edit.comment_text = form.comment.data
        elif content_type == "reply":
            comment_to_edit.reply_text = form.comment.data
        db.session.commit()
        return redirect(url_for("show_post", post_title=post_title))

    return render_template("edit-comment.html", form=form)


@app.route("/delete-post/<int:post_id>", methods=["GET", "POST"])
@role_required(["admin"])
def delete_post(post_id):
    post_to_delete = BlogPost.query.filter_by(id=post_id).first()
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/admin")
@role_required(["admin"])
def admin():
    all_users = User.query.all()
    return render_template("admin.html", all_users=all_users, User=User)


@app.route("/profile", methods=["POST", "GET"])
@login_required
def profile():

    # Find the user profile
    user_to_edit = User.query.filter_by(id=current_user.id).first()

    information_form = UpdateUserInformationForm(username=current_user.username, email=current_user.email)
    password_form = UpdateUserPasswordForm()

    if information_form.submit_info.data and information_form.validate():

        # Check if the username is new and not taken and update the db or revoke the changes
        if information_form.username.data != current_user.username:
            if User.query.filter_by(username=information_form.username.data).first():
                flash("Username Taken")
            else:
                user_to_edit.username = information_form.username.data
                flash("Username changed successfully!")

        # Check if the email is new and not taken and update the db or revoke the changes
        if information_form.email.data != current_user.email:
            if User.query.filter_by(email=information_form.email.data).first():
                flash("Email Taken")
            else:
                user_to_edit.email = information_form.email.data
                flash("Email changed successfully!")

        # Upload profile image
        new_profile_image = information_form.file.data
        if not allowed_file(new_profile_image.filename):
            flash(f"File not allowed. Allowed formats - {ALLOWED_EXTENSIONS} ")
            return redirect(url_for('profile'))

        if new_profile_image:
            profile_image_name = f"{current_user.username}_" + secure_filename(new_profile_image.filename)

            # Check if the user has uploaded a profile picture and delete it before saving the new image
            profile_image_path = os.path.join(app.config["UPLOAD_FOLDER"], "profile_images", current_user.profile_image)
            if os.path.exists(profile_image_path) and current_user.profile_image != "default-avatar.jpg":
                os.remove(profile_image_path)

            new_profile_image.save(os.path.join(app.config["UPLOAD_FOLDER"], "profile_images", profile_image_name))
            user_to_edit.profile_image = profile_image_name
            flash("Profile image changed successfully")
        db.session.commit()
        return redirect(url_for('profile'))

    if password_form.submit_password.data and password_form.validate():
        # Check if the provided password matches the saved in the db
        if check_password_hash(user_to_edit.password, password_form.current_password.data):
            user_to_edit.password = generate_password_hash(password_form.new_password.data, salt_length=8)
            flash("Password changed successfully!")
            db.session.commit()
        else:
            flash("Wrong Password")
        return redirect(url_for('profile'))

    return render_template("profile.html", information_form=information_form, password_form=password_form)


@app.route("/change_role/<int:user_id>/<new_role>")
@role_required(["admin"])
def change_role(user_id, new_role):
    user = User.query.filter_by(id=user_id).first()
    if user.roles != "admin":
        if new_role != user.roles:
            user.roles = new_role
            db.session.commit()
            flash(f'Role for {user.username} successfully changed to {new_role}')
        else:
            flash(f'{user.username} is already {user.roles}')
    else:
        flash(f"{user.username} is Admin, can't change role")

    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
