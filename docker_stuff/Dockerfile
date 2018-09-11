FROM python:3
RUN apt-get update && apt-get install -y \
    software-properties-common
RUN apt-get update && apt-get install -y \
	python3-pip
RUN pip3 install requests
ENTRYPOINT ["python3", "/usr/src/app/pyrunner.py"]