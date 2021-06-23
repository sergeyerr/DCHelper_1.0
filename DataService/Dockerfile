FROM python
WORKDIR /data_service
COPY . /data_service
RUN pip install -r requirements.txt 
ENTRYPOINT ["uvicorn"]
CMD ["DataService:app", "--host",  "0.0.0.0"]