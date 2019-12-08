#!/bin/bash

# uses httpie  - pip3 install httpie
#read -p "username > " user_name
#read -p "password > " pass_word


http POST http://localhost:5000/api/users username=jj password=foo123 \
    email=jj@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=lh password=foo123 \
    email=lh@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=lm password=foo123 \
    email=lm@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=po password=foo123 \
    email=po@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=ab password=foo123 \
    email=ab@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=kr password=foo123 \
    email=kr@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=mb password=foo123 \
    email=mb@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=je password=foo123 \
    email=je@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=kb password=foo123 \
    email=kb@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=nl password=foo123 \
    email=nl@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=mn password=foo123 \
    email=mn@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=af password=foo123 \
    email=af@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=jb password=foo123 \
    email=jb@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=jh password=foo123 \
    email=jh@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=ha password=foo123 \
    email=ha@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=gk password=foo123 \
    email=gk@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=ad password=foo123 \
    email=ad@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=pv password=foo123 \
    email=pv@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=ta password=foo123 \
    email=ta@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=cl password=foo123 \
    email=cl@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=aj password=foo123 \
    email=aj@certificateservices.se "about_me=well certs and stuff!"

http POST http://localhost:5000/api/users username=lu password=foo123 \
    email=lu@certificateservices.se "about_me=well certs and stuff!"
