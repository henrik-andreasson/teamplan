

if [ -f variables ] ; then
  . variables
  echo "URL: ${API_URL}"
  echo "User: ${API_USER}"

fi

token=""
if [ -f rest-get-token.sh ] ; then
  . rest-get-token.sh
  token=$(get_new_token)
  if [ $? -ne 0 ] ; then
    echo "failed to get a login token"
    exit
  fi
else
  echo "login/get token failed"
  exit
fi

if [ "x$1" != "x" ] ; then
    csvfile=$1
else
    echo "arg1 must be a file with location definitions in it"
    echo "username,servicename"
    exit
fi


IFS=$'\n'
for row in $(cat "${csvfile}") ; do

  username=$(echo $row | cut -f1 -d\,)
  servicename=$(echo $row | cut -f2 -d\,)
  iscomment=$(echo $row | grep "^#" )
  if [ "x$iscomment" != "x" ] ; then
    continue
  fi

  http --verify cacerts.pem --verbose "${API_URL}/service/${servicename}/manager/${username}" \
    "Authorization:Bearer $token"

done
