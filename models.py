from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """Represents users of the application."""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    date_joined = db.Column(db.Date, default=datetime.utcnow)
    profile_image = db.Column(db.String, default="default-avatar.jpg")
    roles = db.Column(db.String, default="reader")

    # One-to-many relationship with blog posts authored by the user
    blog_posts = db.relationship("BlogPost", backref="user")

    # One-to-many relationship with comments posted by the user
    comments = db.relationship("Comment", backref="user")

    # One-to-many relationship with comment replies posted by the user
    replies = db.relationship("CommentReplies", backref="user")

    def can(self, roles):
        """Checks if the user has the specified role."""
        return any(role in self.roles for role in roles)


class BlogPost(db.Model):
    """Represents individual blog posts."""
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    subtitle = db.Column(db.String)
    img_url = db.Column(db.String)
    body = db.Column(db.Text)
    posted_on = db.Column(db.Date, default=datetime.utcnow())

    # Foreign key referencing the user who authored the blog post
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # One-to-many relationship with comments associated with the blog post
    comments = db.relationship("Comment", backref="blogpost")


class Comment(db.Model):
    """Represents comments posted by users on blog posts."""
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.String)
    posted_on = db.Column(db.Date, default=datetime.utcnow())

    # Foreign key referencing the user who posted the comment
    commenter = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Foreign key referencing the blog post to which the comment belongs
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))

    # One-to-many relationship with comment replies associated with the comment
    comment_replies = db.relationship("CommentReplies", backref="comment")


class CommentReplies(db.Model):
    """Represents replies to comments posted by users."""
    __tablename__ = "comment replies"
    id = db.Column(db.Integer, primary_key=True)
    reply_text = db.Column(db.String)
    posted_on = db.Column(db.Date, default=datetime.utcnow())

    # Foreign key referencing the comment to which the reply belongs
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"))

    # Foreign key referencing the user who posted the reply
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
