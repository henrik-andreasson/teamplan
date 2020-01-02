#!/bin/bash

# uses httpie  - pip3 install httpie
read -p "username > " user_name
read -p "password > " pass_word
read -p "service > " service
if [ "x$1" != "x" ] ; then
    days=$1
else
    echo "arg1 must be a file with days"
    exit
fi

token=$(http --auth "$user_name:$pass_word" POST http://localhost:5000/api/tokens | jq ".token")


for row in $(cat $csv) ; do
# 2020-01-31;08:00;12:30;cs;ab
  date=$(cut -f1 -d\;)
  starttime=$(cut -f2 -d\;)
  stoptime=$(cut -f3 -d\;)
  service=$(cut -f4 -d\;)
  assagniee=$(cut -f5 -d\;)

  http --verbose POST http://localhost:5000/api/work service=$service \
    start="$date $starttime" stop="$date $stoptime" username="$assagniee" \
     "Authorization:Bearer $token"

  sleep 1

done
