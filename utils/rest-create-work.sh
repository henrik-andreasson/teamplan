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

if [ "x$1" != "x" ] ; then
    csvfile=$1
else
    echo "arg1 must be a file with location definitions in it"
    echo "username,servicename"
    exit
fi


for row in $(cat $csvfile) ; do
  echo "row: $row"
  date=$(echo $row | cut -f1 -d\,)
  starttime=$(echo $row | cut -f2 -d\,)
  stoptime=$(echo $row | cut -f3 -d\,)
  username=$(echo $row | cut -f4 -d\,)
  servicename=$(echo $row | cut -f5 -d\,)

  if [ "x$username" == "xunassigned" ] ; then

    http  --verbose POST "${API_URL}/work" service_name="$servicename" \
      start="$date $starttime" stop="$date $stoptime" status="unassigned" \
      "Authorization:Bearer $token"
  else
    http  --verbose POST "${API_URL}/work" service_name="$servicename" \
      start="$date $starttime" stop="$date $stoptime" status="assigned" user_name="$username" \
      "Authorization:Bearer $token"
  fi


#  sleep 1

done
