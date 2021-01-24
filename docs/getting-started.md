# Manual install on CentOS

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

See the `first time create db below`

# Run in Docker

git checkout

    git checkout https://github.com/henrik-andreasson/teamplan.git

build docker:

    docker build -t teamplan  .

Run docker interactive (remove -it to run in background)

    docker run --name teamplan -p5000:5000 -it  teamplan flask run --host=0.0.0.0 --reload

Run docker for development

    docker run --name teamplan -p5000:5000 -it  --mount type=bind,source="$(pwd)",target=/teamplan teamplan flask run --host=0.0.0.0 --reload

Check running docker containers

    docker ps

Start bash shell in the teamplan container to

    docker exec -it containername bash  

See the `first time create db below` to get going first time

# First time to create databse

First step in getting flask db started

    flask db init

Second steps, these will be needed when schema upgrades are needed in the future

    flask db migrate -m name-of-the-upgrade
    flask db upgrade


# Use mariadb instead of sqlite

set the environment variable: `SQLALCHEMY_DATABASE_URI`

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://teamplan:foo123@172.17.0.4/teamplan'

# set custom sqlite db

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
