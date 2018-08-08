import os
import re
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, escape

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///mashup.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")

