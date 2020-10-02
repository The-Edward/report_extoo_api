FROM python:3.8
LABEL MAINTAINER="TheEdward"
COPY . /app
WORKDIR /app
RUN pip install -r /app/requirements.txt
CMD [ "python", "./runner.py" ]
EXPOSE 5050
