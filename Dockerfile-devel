# Use an official Python runtime as a parent image
FROM centos:latest

# Set the working directory to /app
WORKDIR /teamplan

# Install any needed packages
RUN yum install -y python3 sqlite

RUN pip3 install flask-sqlalchemy flask-migrate flask-login flask-mail \
  flask-bootstrap flask-moment flask-babel python-dotenv jwt flask-wtf \
  WTForms-Components flask-httpauth rocketchat_API icalendar gunicorn

# Make port 8000 available to the world outside this container
EXPOSE 5000

ENV FLASK_APP=teamplan.py
# Run flask when the container launches
CMD [ "flask run --host=0.0.0.0"]
