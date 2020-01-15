#!/bin/bash

# uses httpie  - pip3 install httpie

user_name="admin"
pass_word="foo123"

token=$(http --auth "$user_name:$pass_word" POST http://localhost:5000/api/tokens | jq ".token")


http --verbose http://localhost:5000/api/worklist \
      "Authorization:Bearer $token"
