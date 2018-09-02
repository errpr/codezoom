import os
import re
import bcrypt
import docker
import random
import string
import datetime
from time import sleep
from flask import Flask, jsonify, flash, render_template, request, session, redirect, url_for, escape
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
from models.problem import Problem 
from models.test import Test

docker_client = docker.from_env()
engine = create_engine('sqlite:///app.db', echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(engine)
dbsession = DBSession()
dbsession.close()

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.secret_key = os.environ["FLASK_SECRET"]
socketio = SocketIO(app)

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

@app.route("/room", methods=["GET", "POST"])
def room():
    if not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()    
    if not user:
        session["user_id"] = None
        return redirect("/login")

    if request.method == "POST":
        if not request.form.get("code"):
            flash("Requires code to test")
            return redirect("/room")

        #random name for file
        filename = ''.join(random.choices(string.ascii_uppercase, k=9)) + ".py"
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/dangeroux'
        
        #get tests
        #TODO
        test_args = ["hello", "world"]
        returned = b""
        
        #copy code into file
        with open("./dangeroux/" + filename, "w") as f:
            f.write(request.form.get("code"))

        try:
            #run code in docker container and hope its safe lol
            container = docker_client.containers.run("python:3",
                                                    ["python", filename, *test_args],
                                                    volumes={ dir_path: {'bind': '/usr/src/app', 'mode': 'ro'}},
                                                    working_dir='/usr/src/app',
                                                    detach=True,
                                                    remove=True)
            print(container)

            time_started = datetime.datetime.now()
            time_to_kill = time_started + datetime.timedelta(seconds=5)

            completed = False
            while(datetime.datetime.now() < time_to_kill):
                if not container.logs() == b"":
                    completed = True
                    break

            print("container logs:")
            print(container.logs())
            returned = container.logs()
            
            if not completed:
                print("Program did not output in time")
                container.stop(timeout=1)

        except Exception as e:
            print("Docker run failed!")
            print(str(e))
        finally:    
            #delete code file
            os.remove("./dangeroux/" + filename)

        flash(returned.decode('ascii'))
    return render_template("room.html")

@app.route("/problems", methods=["GET", "POST"])
def problems():
    if not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    # Validate all the things
    if request.method == "POST":
        if not request.form.get("title"):
            flash("Title is required")
            return redirect("/problems")
        if not request.form.get("description"):
            flash("Description is required")
            return redirect("/problems")
        
        new_problem = Problem(title=request.form.get("title"),
                              description=request.form.get("description"),
                              user_id=user.id)
        
        dbsession.add(new_problem)
        dbsession.commit()
        flash("New problem created successfully")
        return redirect("/problems/" + str(new_problem.id))

    return render_template("problems.html", user=user)

@app.route("/problems/new")
def problem_new():
    if not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    return render_template("problem_new.html", user=user)

@app.route("/problems/<int:problem_id>", methods=["GET", "POST"])
def problem_edit(problem_id):
    if not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    problem = dbsession.query(Problem).filter(Problem.id == problem_id).first()
    if not problem.user_id == user.id:
        return 403

    if request.method == "POST":
        if request.form.get("title"):
            problem.title = request.form.get("title")
        if request.form.get("description"):
            problem.description = request.form.get("description")

        dbsession.commit()

    return render_template("problem_edit.html", user=user, problem=problem)

# should only be called by XHR
@app.route("/problems/<int:problem_id>/tests/<int:test_id>", methods=["POST"])
def test_edit(problem_id, test_id):
    if not session["user_id"]:
        return "403 Forbidden"

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()

    problem = dbsession.query(Problem).filter(Problem.id == problem_id).first()
    if not problem.user_id == user.id:
        return "403 Forbidden"

    test = dbsession.query(Test).filter(Test.id == test_id).first()
    if not test.problem_id == problem_id:
        return "500 Something bad happened"

    if request.form.get("input"):
        test.input = request.form.get("input")

    if request.form.get("output"):
        test.output = request.form.get("output")

    dbsession.commit()

    return "200 OK"

# should only be called by XHR
@app.route("/problems/<int:problem_id>/tests/new", methods=["POST"])
def test_create(problem_id):
    if not session["user_id"]:
        return "403 Forbidden"

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    problem = dbsession.query(Problem).filter(Problem.id == problem_id).first()
    if not problem.user_id == user.id:
        return "403 Forbidden"

    new_test = Test(input=request.form.get("input"),
                    output=request.form.get("output"),
                    problem_id=problem.id)
    dbsession.add(new_test)
    dbsession.commit()

    return str(new_test.id)

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

if __name__ == '__main__':
    socketio.run(app)