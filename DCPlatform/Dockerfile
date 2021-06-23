FROM python:3.7
WORKDIR /dcp
COPY . /dcp
ENV FLASK_APP=DCPlatform.py
RUN pip install -r requirements.txt 
RUN python preload.py
ENTRYPOINT ["flask", "run", "--host", "0.0.0.0"]
