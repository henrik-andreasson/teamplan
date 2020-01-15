#!/bin/bash

# uses httpie  - pip3 install httpie
#read -p "username > " user_name
#read -p "password > " pass_word

http --verbose POST http://localhost:5000/api/service name=cashier color="#FF9999"

http --verbose POST http://localhost:5000/api/service name=storage color="#99FF99"

http --verbose POST http://localhost:5000/api/service name=truck color="#9999FF"

http --verbose POST http://localhost:5000/api/service name=shoes color="#FF3333"
