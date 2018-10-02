import os
import re
import bcrypt
import docker
import random
import string
import datetime
import json

from time import sleep
from flask import Flask, jsonify, flash, render_template, request, session, redirect, url_for, escape
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.user import User
from models.problem import Problem 
from models.test import Test
from models.run import Run
from models.room import Room, RoomProblem

docker_client = docker.from_env()
engine = create_engine('sqlite:///app.db', echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(engine)
dbsession = DBSession()

# PUT FIXTURES HERE
# Apply fixtures if db is empty
if not dbsession.query(User).first():
    print("EMPTY DB DETECTED - APPLYING FIXTURES")
    global_problems_user = User(name="global", pw_hash=bcrypt.hashpw(os.environ['CODEZOOM_GLOBAL_USER_PW'].encode('ascii'), bcrypt.gensalt()))
    global_problems_user.problems = [
        Problem(
            title="Reverse a string", 
            description="String goes STDIN, string comes STDOUT reversed, you can't explain that!",
            tests=[
                Test(input="Hello", output="olleH"),
                Test(input="World", output="dlroW"),
                Test(input="Hello world!", output="!dlrow olleH")
            ]
        )
    ]
    dbsession.add(global_problems_user)
    dbsession.commit()

dbsession.close()

# @ROBUSTNESS this is language specific to python and a hack
DEFAULT_CODE = "import sys\n\n# print out first command line argument\nprint(sys.argv[1])"

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.secret_key = os.environ["FLASK_SECRET"]

def generate_room_id(db):
    possible_string = ''
    while(True):
        possible_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        room = db.query(Room).filter(Room.id == possible_string).first()
        if not room:
            break
    return possible_string

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

@app.route("/rooms")
def rooms():
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    return render_template("room_index.html", user=user)

@app.route("/rooms/new", methods=["GET", "POST"])
def room_new():
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    if request.method == "POST":

        if not request.form.get("problems"):
            flash("Cannot create room without problems.")
            return redirect("/rooms")

        if not request.form.get("password"):
            flash("Cannot create room without password.")
            return redirect("/rooms")

        room = Room(id=generate_room_id(dbsession),
                    owner_id=session["user_id"],
                    password=request.form.get("password"))
        problem_ids = request.form.get("problems").split(",")
        for index, problem_id in enumerate(problem_ids):
            rp = RoomProblem(room_id=room.id, problem_id=problem_id, order_id=index)
            dbsession.add(rp)
            room.problems.append(rp)

        dbsession.add(room)
        dbsession.commit()
        print(room)
        return room.id

    # GET
    user_problems = dbsession.query(Problem).filter(Problem.user_id == user.id)
    global_problems = dbsession.query(Problem).filter(Problem.user_id == 1)

    return render_template("room_new.html", user_problems=user_problems, global_problems=global_problems)


@app.route("/rooms/<string:room_id>")
@app.route("/rooms/<string:room_id>/")
def room_base(room_id):
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    room = dbsession.query(Room).filter(Room.id == room_id).first()
    if not room:
        flash("Room not found")
        return redirect("/")

    return render_template("room_base.html", room=room)


@app.route("/rooms/<string:room_id>/admin")
def room_admin(room_id):
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    room = dbsession.query(Room).filter(Room.id == room_id).first()
    if not room:
        flash("Room not found")
        return redirect("/")

    if not room.owner_id == user.id:
        return redirect("/rooms/" + str(room_id))
    return render_template("room_admin.html", room=room)


@app.route("/rooms/<string:room_id>/complete")
def room_complete(room_id):
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    room = dbsession.query(Room).filter(Room.id == room_id).first()
    if not room:
        flash("Room not found")
        return redirect("/")

    return render_template("room_complete.html", room=room)


@app.route("/rooms/<string:room_id>/<int:problem_order_id>", methods=["GET", "POST"])
def room_problem(room_id, problem_order_id):
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    room = dbsession.query(Room).filter(Room.id == room_id).first()
    if not room:
        flash("Room not found")
        return redirect("/")

    problem = room.problems[problem_order_id].problem
    if not problem:
        flash("Problem not found")
        return redirect("/rooms/" + room.id)

    # next_id used in UI to link to the next problem
    next_id = problem_order_id + 1
    if len(room.problems) <= next_id:
        next_id = "complete"

    if request.method == "POST":
        if not request.form.get("code"):
            flash("Requires code to test")
            return redirect("/rooms")

        #random name for files and directory
        file_id = ''.join(random.choices(string.ascii_uppercase, k=9))

        runner_path = os.path.dirname(os.path.realpath(__file__)) + '/docker_stuff'
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/dangeroux'

        #create run in database
        run = Run(  file_id=file_id, 
                    problem_id=problem.id,
                    room_id=room.id,
                    user_id=user.id,
                    code=request.form.get("code"))
        dbsession.add(run)

        #copy tests into file
        with open(dir_path + "/" + file_id + ".testfile", "w") as f:
            for test in problem.tests:
                f.write(test.input + "\uFFFF" + test.output + "\n")
        
        # @ROBUSTNESS this shouldn't be hardcoded to run python
        #copy code into file
        with open(dir_path + "/" + file_id + ".py", "w") as f:
            f.write(request.form.get("code"))

        # @ROBUSTNESS this shouldn't be hardcoded to run python
        #run code in docker container and hope its safe lol
        c = docker_client.containers.run("errpr/pyrunner",
                                         [file_id],
                                         volumes={ dir_path: {'bind': '/usr/src/data', 'mode': 'ro'},
                                                   runner_path: {'bind': '/usr/src/app', 'mode': 'ro'}},
                                         working_dir='/usr/src/data',
                                         network_mode="host",
                                         detach=True,
                                         remove=True)
        dbsession.commit()
        return file_id

    #GET
    return render_template("room_problem.html", 
                            room=room, 
                            problem=problem, 
                            next_id=next_id, 
                            code_prefill=DEFAULT_CODE, 
                            code_length=len(DEFAULT_CODE))

#post results of runs here from the docker container
#get results of runs here from the UI
@app.route("/run_results/<string:run_id>", methods=["GET", "POST"])
def run_results(run_id):
    if request.method == "POST":
        results = json.JSONDecoder().decode(str(request.json))
        print(results)
        run = dbsession.query(Run).filter(Run.file_id == run_id).first()
        run.output = request.json

        success_count = 0
        for result in results:
            if result[1]:
                success_count += 1

        # honestly the only way I can think of to count children :|
        test_count = 0
        for test in run.problem.tests:
            test_count += 1

        run.success_count = success_count
        run.successful = success_count == test_count
        dbsession.commit()

        # clean up files
        os.remove("./dangeroux/" + run_id + ".py")
        os.remove("./dangeroux/" + run_id + ".testfile")

        return "0"
    
    #GET
    else:
        run = dbsession.query(Run).filter(Run.file_id == run_id).first()

        if run.output:
            return json.JSONEncoder().encode({ "output": run.output, "success_count": run.success_count, "full_success": run.successful })
        return "0"


# should be XHR only
# get admin panel info here
@app.route("/room_results/<string:room_id>")
def room_results(room_id):
    if not session or not session["user_id"]:
        return "300 Forbidden"

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return "300 Forbidden"

    room = dbsession.query(Room).filter(Room.id == room_id).first()
    if not room:
        return "404 Not Found"

    if not room.owner.id == user.id:
        return "300 Forbidden"

    # create a map of each user to their
    # most recent runs for each problem
    user_run_map = { 'user_list': [] }
    query = dbsession.query(Run, func.max(Run.time_created)).filter(Run.room_id == room.id).group_by(Run.user_id, Run.problem_id)
    
    for row in query.all():
        run = row[0]

        problem_order_id = 0
        for problem in run.room.problems:
            if problem.problem_id == run.problem_id:
                problem_order_id = problem.order_id
                break

        user = dbsession.query(User).filter(User.id == run.user_id).first()
        if user.name in user_run_map:
            user_run_map[user.name]['problem_list'].append(str(problem_order_id))
            user_run_map[user.name][str(problem_order_id)] = {
                'successful': run.successful,
                'success_count': run.success_count,
                'time_created': run.time_created.timestamp()
            }
        else:
            user_run_map['user_list'].append(user.name)
            user_run_map[user.name] = {
                'problem_list': [str(problem_order_id)],
                str(problem_order_id): {
                    'successful': run.successful,
                    'success_count': run.success_count,
                    'time_created': run.time_created.timestamp()
                }
            }

    return json.JSONEncoder().encode(user_run_map)



@app.route("/problems", methods=["GET", "POST"])
def problems():
    if not session or not session["user_id"]:
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
    
    #GET
    return render_template("problem_index.html", user=user)

@app.route("/problems/new")
def problem_new():
    if not session or not session["user_id"]:
        return redirect("/login")

    user = dbsession.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        session["user_id"] = None
        return redirect("/login")

    return render_template("problem_new.html", user=user)

@app.route("/problems/<int:problem_id>", methods=["GET", "POST"])
def problem_edit(problem_id):
    if not session or not session["user_id"]:
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
    if not session or not session["user_id"]:
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
    if not session or not session["user_id"]:
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

    return json.JSONEncoder().encode({"id": new_test.id, "input": new_test.input, "output": new_test.output})

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