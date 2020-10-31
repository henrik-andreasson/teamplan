#!/bin/bash

user_name="andreassonhe"
pass_word="foo123"

url=http://164.9.195.130

if [ "x$1" != "x" ] ; then
    days=$1
else
    echo "arg1 must be a file with days"
    exit
fi

if [ "x$2" != "x" ] ; then
    services=$2
else
    echo "arg2 must be a file with services"
    exit
fi

token=$(http --auth "$user_name:$pass_word" POST $url/api/tokens | jq ".token")



for service in $(cat $services) ; do
  for day in $(cat $days) ; do

    http --verbose POST $url/api/work service=$service \
      start="$day 08:00" stop="$day 12:30"  \
      "Authorization:Bearer $token"

     http --verbose POST $url/api/work service=$service \
       start="$day 12:30" stop="$day 17:00"  \
       "Authorization:Bearer $token"

    done

done
