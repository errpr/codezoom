# codezoom

Codezoom is a programming teaching aid. Teachers create problems by specifying input and expected output, then add problems to a room. Students join the room and write code that produces the desired output for each problem.

Requires python3 and docker

# Directions

Clone the repository:

`git clone https://github.com/errpr/codezoom.git`

Install packages from pip:

`pip3 install -r requirements.txt`

Then 
```
export FLASK_APP=application.py
export FLASK_SECRET=<some secret>
export CODEZOOM_GLOBAL_USER_PW=<password for global problem pool user>
```

After that you're ready to run, but the application needs `sudo` in order to do docker things so the invocation I use is: 

`sudo --preserve-env python3 -m flask run`