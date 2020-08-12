#!/bin/bash

gunicorn teamplan:app -b 0.0.0.0:8080 \
         --pid /teamplan/teamplan.pid 
