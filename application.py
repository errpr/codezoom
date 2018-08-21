import os
import re
from flask import Flask, jsonify, flash, render_template, request, session, redirect, url_for, escape
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
import bcrypt

engine = create_engine('sqlite:///app.db', echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(engine)
dbsession = DBSession()
dbsession.close()

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.secret_key = os.environ["FLASK_SECRET"]

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    dbsession.close()
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.before_request
def before_request():
    dbsession = DBSession()

@app.route("/")
def index():
    
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.form.get("inputUsername1"):
            flash("Username required")
            return redirect("/login")
        if not request.form.get("inputPassword1"):
            flash("Password required")
            return redirect("/login")
        exists = dbsession.query(User).filter(User.name == request.form.get("inputUsername1")).first()
        if exists:
            if bcrypt.checkpw(request.form.get("inputPassword1").encode(), exists.pw_hash):
                session["user_id"] = exists.id
                flash("Successfully logged in")
                return redirect("/")
        flash("Incorrect password or username")
        return redirect("/login")

    return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    session["user_id"] = None
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        for element in request.form:
            print(element)
        if not request.form.get("inputUsername1"):
            flash("Username required")
            return redirect("/register")
        
        elif not request.form.get("inputPassword1"):
            flash("Password required")
            return redirect("/register")
        
        elif not request.form.get("inputConfirm1"):
            flash("Password confirmation required")
            return redirect("/register")
        
        elif not request.form.get("inputConfirm1") == request.form.get("inputPassword1"):
            flash("Password must match confirmation")
            return redirect("/register")

        exists = dbsession.query(User).filter(User.name == request.form.get("inputUsername1")).first()
        print(exists)
        if exists:
            flash("Username already exists")
            return redirect("/register")

        #insert user into db and set session
        pw_hash = bcrypt.hashpw(request.form.get("inputPassword1").encode(), bcrypt.gensalt())
        new_user = User(name=request.form.get("inputUsername1"), fullname=request.form.get("inputUsername1"), pw_hash=pw_hash)
        dbsession.add(new_user)
        dbsession.commit()

        session["user_id"] = new_user.id
        flash("Created account and logged in successfully.")
        return redirect("/")

    return render_template("register.html")