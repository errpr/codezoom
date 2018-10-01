# Usage: pyrunner.py <file_id>
# Runs the python script <file_id>.py with input from <file_id>.testfile and compares its output against <file_id>.testfile, then posts results to the server

import sys
import os
import subprocess
import requests
import json

file_id = sys.argv[1]

with open(file_id + '.testfile', "r") as f:
  test_file = f.read()

test_file = test_file.split('\n')
results = []

for line in test_file:
  if line == '' or line == '\n':
    continue

  line2 = line.split("\uFFFF")
  inpt = line2[0]
  outpt = line2[1]

  try:
    returned = subprocess.run(["python3", file_id + ".py", inpt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=True)
    results.append([returned.stdout.decode('ascii').rstrip(), returned.stdout.decode('ascii').rstrip() == outpt])

  except subprocess.TimeoutExpired:
    results.append(["dnf", False])

  except subprocess.CalledProcessError as e:
    results.append(["Process failure:\n" + e.stderr.decode('ascii'), False])

r = requests.post("http://127.0.0.1:5000/run_results/" + file_id, json=json.JSONEncoder().encode(results))