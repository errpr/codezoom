# codezoom

Codezoom is a programming teaching aid. Create problems by specifying input and expected output, then add problems to a room. Students join the room and write code that produces the desired output for each problem.

Requires python3 and docker

# Directions

Install packages from pip. 

Then `export FLASK_APP=application.py` and `export FLASK_SECRET=<some secret>`.

After that you're ready to run, but the application needs `sudo` in order to do docker things so the invocation I use is: `sudo --preserve-env python3 -m flask run`