FROM python
WORKDIR /runner_service
COPY . /runner_service
RUN pip install -r requirements.txt 
ENTRYPOINT ["uvicorn"]
CMD ["RunnerService:app", "--host",  "0.0.0.0"]