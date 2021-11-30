FROM python:3.7-slim-buster
RUN apt update
RUN apt-get install curl -y

WORKDIR ./
COPY ./models .
COPY ./module .
COPY compressed_Table.py .
COPY config.py .
COPY db_driver.py .
COPY lion_detector.py .
COPY lion_model.py .
COPY prepare_train_data.py .
COPY requirements.txt .
COPY service.py .
COPY train_model.py .
COPY train_utils.py .
COPY utils.py .
RUN pip install -r ./requirements.txt
EXPOSE 8080
#Run the application
CMD ["python","service.py"]
