#!/bin/bash

# uses httpie  - pip3 install httpie
#read -p "username > " user_name
#read -p "password > " pass_word


http POST http://localhost:5000/api/users username=admin password=foo123 \
    email="admin@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user1 password=foo123 \
    email="user1@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user2 password=foo123 \
    email="user2@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user3 password=foo123 \
    email="user3@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user4 password=foo123 \
    email="user4@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user5 password=foo123 \
    email="user5@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user6 password=foo123 \
    email="user6@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user7 password=foo123 \
    email="user7@example.com" "about_me=well me and stuff!"

http POST http://localhost:5000/api/users username=user8 password=foo123 \
    email="user8@example.com" "about_me=well me and stuff!"
