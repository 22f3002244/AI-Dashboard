from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, session
from models.database import db, User
from functools import wraps

main = Blueprint("main", __name__)

# Login required decorator
def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not in session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def home():
    return render_template("index.html")

@main.route('/login', methods=["GET"])
def login():
    return render_template("auth/login.html")

@main.route('/chat')
@login_required
def chat():
    user = User.query.get(session['user_id'])
    return render_template("user/chat.html", user=user)

@main.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template("user/dashboard.html", user=user)

@main.route('/projects/drafts')
@login_required
def drafts():
    user = User.query.get(session['user_id'])
    return render_template("user/draft.html", user=user)

@main.route('/my-projects')
@login_required
def projects():
    user = User.query.get(session['user_id'])
    return render_template("user/projects.html", user=user)

@main.route('/Sign-Up', methods=["GET"])
def SignUp():
    return render_template("auth/register.html")

@main.route('/Settings')
@login_required
def Settings():
    user = User.query.get(session['user_id'])
    return render_template("user/settings.html", user=user)

#----------------------------POST ROUTES---------------------------------

@main.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid email or password", "danger")
        return redirect(url_for("main.login"))

    session['user_id'] = user.id
    flash("Login successful", "success")
    return redirect(url_for("main.chat"))

@main.route("/register", methods=["POST"])
def register_post():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered", "danger")
        return redirect(url_for("main.SignUp"))

    user = User(firstname=first_name, lastname=last_name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("main.login"))

@main.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully", "success")
    return redirect(url_for("main.home"))

@main.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    try:
        # Get the current user
        user = User.query.get(session['user_id'])
        
        if user:
            # Delete the user from database
            db.session.delete(user)
            db.session.commit()
            
            # Clear the session
            session.pop('user_id', None)
            
            flash("Your account has been deleted successfully.", "success")
            return redirect(url_for("main.home"))
        else:
            flash("User not found.", "danger")
            return redirect(url_for("main.Settings"))
            
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting account: {str(e)}")
        flash("An error occurred while deleting your account. Please try again.", "danger")
        return redirect(url_for("main.Settings"))
    
@main.route("/change-password", methods=["POST"])
@login_required
def change_password():
    try:
        # Get form data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Get current user
        user = User.query.get(session['user_id'])
        
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Verify current password
        if not user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Check password length
        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        flash("Password updated successfully!", "success")
        return redirect(url_for("main.Settings"))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error changing password: {str(e)}")
        flash("An error occurred while changing your password. Please try again.", "danger")
        return redirect(url_for("main.Settings"))


@main.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    try:
        # Get form data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        
        # Validate inputs
        if not first_name or not last_name:
            flash("First name and last name are required.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Get current user
        user = User.query.get(session['user_id'])
        
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("main.Settings"))
        
        # Update user information
        user.firstname = first_name
        user.lastname = last_name
        db.session.commit()
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for("main.Settings"))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile: {str(e)}")
        flash("An error occurred while updating your profile. Please try again.", "danger")
        return redirect(url_for("main.Settings"))