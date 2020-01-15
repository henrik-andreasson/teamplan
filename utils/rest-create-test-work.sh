#!/bin/bash

# uses httpie  - pip3 install httpie

user_name="admin"
pass_word="foo123"

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

token=$(http --auth "$user_name:$pass_word" POST http://localhost:5000/api/tokens | jq ".token")


for service in $(cat $services) ; do
  for day in $(cat $days) ; do

    work_user=$(shuf -n1 "$service-users.txt")
    http --verbose POST http://localhost:5000/api/work service=$service \
      start="$day 08:00" stop="$day 12:30" username="$work_user" \
      "Authorization:Bearer $token"

      work_user=$(shuf -n1 "$service-users.txt")
      http --verbose POST http://localhost:5000/api/work service=$service \
        start="$day 12:30" stop="$day 17:00" username="$work_user" \
        "Authorization:Bearer $token"

    done

done
