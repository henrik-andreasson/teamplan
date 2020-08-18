#!/bin/bash

read -p "username > " user_name
read -p "password > " pass_word

url="https://schema.certificateservices.se"

if [ "x$1" != "x" ] ; then
    days=$1
else
    echo "arg1 must be a file with days"
    exit
fi

if [ "x$2" != "x" ] ; then
    service=$2
else
    echo "arg2 must be the service to add work for"
    exit
fi

token=$(http --verify=false --auth "$user_name:$pass_word" POST $url/api/tokens | jq ".token" | sed 's/"//g')



for day in $(cat $days) ; do

    http --verify=false --verbose POST $url/api/work service=$service \
      start="$day 08:00" stop="$day 12:30"  \
      "Authorization:Bearer $token"

     sleep 5

     http --verify=false --verbose POST $url/api/work service=$service \
       start="$day 12:30" stop="$day 17:00"  \
       "Authorization:Bearer $token"

     sleep 5
done
