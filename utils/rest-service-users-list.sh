#!/bin/bash


if [ -f variables ] ; then
  . variables
  echo "URL: ${API_URL}"
  echo "User: ${API_USER}"

fi

token=""
if [ -f rest-get-token.sh ] ; then
  . rest-get-token.sh
  token=$(get_new_token)
  if [ $? -ne 0 ] ; then
    echo "failed to get a login token"
    exit
  fi
else
  echo "login/get token failed"
  exit
fi


if [ "x$1" = "x" ] ; then
  echo "arg1 should be the servicename"
  exit
else
  service="$1"
fi


http --verbose "http://localhost:5000/api/service/${service}/users"\
      "Authorization:Bearer $token"
