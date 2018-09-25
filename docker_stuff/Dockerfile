FROM python:3
RUN apt-get update && apt-get install -y \
    software-properties-common
RUN apt-get update && apt-get install -y \
	python3-pip
RUN pip3 install --trusted-host pypl.org --trusted-host files.pythonhosted.org requests
ENTRYPOINT ["python3", "/usr/src/app/pyrunner.py"]