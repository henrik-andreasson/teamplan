# Use an official Python runtime as a parent image
FROM centos:latest

WORKDIR /teamplan

# Set the working directory to /app
RUN mkdir /teamplan
RUN mkdir /teamplan/logs
RUN mkdir /teamplan/app
COPY . /teamplan/
#COPY teamplan.py /teamplan/
#COPY config.py /teamplan
#COPY app.db /teamplan
#COPY cert.pem /teamplan
#COPY key.pem /teamplan
#COPY ca.pem /teamplan
#COPY docker-start.sh /teamplan/start.sh
#RUN chmod +x /teamplan/start.sh

# Install any needed packages
RUN yum install -y python3 sqlite

RUN pip3 install flask-sqlalchemy flask-migrate flask-login flask-mail \
  flask-bootstrap flask-moment flask-babel python-dotenv jwt flask-wtf \
  WTForms-Components flask-httpauth rocketchat_API icalendar gunicorn

# Make port 8000 available to the world outside this container
EXPOSE 443

ENV FLASK_APP=teamplan.py

CMD [ "/teamplan/gunicorn-start.sh" ]
