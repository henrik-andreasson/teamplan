# Use an official Python runtime as a parent image
FROM debian:latest


WORKDIR /teamplan

# Set the working directory to /app
COPY . /teamplan/

# Install any needed packages
RUN apt-get update

RUN apt-get install --no-install-recommends -y python3 \
        sqlite3 jq python3-pip python3-setuptools  \
        python3-wheel gunicorn3

RUN pip3 install --break-system-packages -U pip
RUN pip3 install --break-system-packages -r requirements.txt

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Make port available to the world outside this container
EXPOSE 8080

COPY gunicorn-http-start.sh /teamplan/start.sh
RUN chmod +x /teamplan/start.sh


ENV FLASK_APP=teamplan.py

CMD [ "/teamplan/start.sh" ]
