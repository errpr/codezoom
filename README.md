# This is a work in progress, it doesn't do much yet.

Requires python3 and docker

# Directions

Install packages from pip. 
Then `export FLASK_APP=application.py` and `export FLASK_SECRET=<some secret>`.
After that you're ready to run, but the application needs `sudo` in order to do docker things so the invocation I use is: `sudo --preserve-env python3 -m flask run`