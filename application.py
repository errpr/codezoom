import os
import re
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, escape
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User

engine = create_engine('sqlite:///:memory:', echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(engine)
dbsession = DBSession()
dbsession.close()

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

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
    """Render map"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST", "DELETE"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST", "DELETE"])
def register():

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Username required")
            return redirect("/register")
        
        elif not request.form.get("password"):
            flash("Password required")
            return redirect("/register")
        
        elif not request.form.get("confirm"):
            flash("Password confirmation required")
            return redirect("/register")
        
        elif not request.form.get("confirm") == request.form.get("password"):
            flash("Password must match confirmation")
            return redirect("/register")

        exists = dbsession.query(User).filter(User.name == request.form.get("username"))
        if len(exists) > 0:
            flash("Username already exists")
            return redirect("/register")

        #insert user into db and set session
        new_user = User()

        return redirect("/")
    elif request.method == "DELETE"
        #remove user from db
        return redirect("/")

    return render_template("register.html")