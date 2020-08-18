#!/bin/bash

get_new_token() {

  if [ -f .token ] ; then
    token_age=$(( $(date +"%s") - $(date -r .token +"%s") ))
    if [ "x$token_age" != "x" ] ; then
      if [ $token_age -lt 3600 ] ; then
        token=$(cat .token)
        echo "using cached token: ${token}, remove .token to force new login" >&2
        echo "${token}"
        return
      fi
    fi
  fi

  if [ "x${API_USER}" == "x" ] ; then
    read -p "username > " user_name
  else
    username="${API_USER}"
  fi

  if [ "x${API_PASS}" == "x" ] ; then
    read -p "password > " pass_word
  else
    password="${API_PASS}"
  fi

  if [ "x${API_URL}" == "x" ] ; then
    apiserverurl="http://127.0.0.1:5000/api"
  else
    apiserverurl="${API_URL}"
  fi

  token=$(http --verify cacerts.pem --auth "$username:$password" POST "${apiserverurl}/tokens" | jq ".token" | sed 's/\"//g')
  if [ "x${token}" != "x" ] ; then
    echo "${token}" > .token
    echo "Got fresh token ${token}" >&2
    echo "${token}"
  else
    echo "failed to login/refresh token" >&2
    exit -1
  fi
}
