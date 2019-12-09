#!/bin/bash

# uses httpie  - pip3 install httpie
read -p "username > " user_name
read -p "password > " pass_word

http --auth "$user_name:$pass_word" POST http://localhost:5000/api/tokens | jq ".token"
