# Run on CentOS

Install python3 and sqlite

    yum install -y python3 sqlite

Used modules

    pip3 install flask-sqlalchemy flask-migrate flask-login flask-mail \
  flask-bootstrap flask-moment flask-babel python-dotenv jwt flask-wtf \
  WTForms-Components flask-httpauth rocketchat_API icalendar gunicorn \
  email_validator PyMysql

install source

    mkdir /opt/teamplan
    cd /opt/teamplan
    unzip teamplan-x.y.z.zip

start
    export FLASK_APP=teamplan.py
    cd /opt/teamplan
    flask run --host=0.0.0.0

See also the systemd service file teamplan.service to run with gunicorn

# Run in Docker

build docker:

    docker build -t teamplan  .

Run bash in docker:

    docker run -p5000:5000 -it  --mount type=bind,source="$(pwd)",target=/teamplan teamplan bash

Run flask

    docker run -p5000:5000 -it  --mount type=bind,source="$(pwd)",target=/teamplan teamplan flask run --host=0.0.0.0 --reload
