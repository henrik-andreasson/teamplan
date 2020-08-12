#!/bin/bash

if [ "x$CERT" != "x" ] ; then
  echo "$CERT" | tr ';' '\n' > /teamplan/cert.pem
fi

if [ "x$CA" != "x" ] ; then
  echo "$CA" | tr ';' '\n' > /teamplan/ca.pem
fi

if [ "x$KEY" != "x" ] ; then
  echo "$KEY" | tr ';' '\n' > /teamplan/key.pem
fi

gunicorn teamplan:app -b 0.0.0.0:443 \
         --pid /teamplan/teamplan.pid \
         --keyfile /teamplan/key.pem  \
         --certfile  /teamplan/cert.pem
