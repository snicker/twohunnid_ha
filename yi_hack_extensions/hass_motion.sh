#!/bin/sh
HASSIP=$HASSIP
HASSAPIKEY=$HASSAPIKEY

CAMERA_NAME=$1
FRIENDLY_NAME=$2
STATE=$3
FILENAME=$4
IP_ADDRESS="$(ifconfig | grep -A 1 'ra0' | tail -1 | cut -d ':' -f 2 | cut -d ' ' -f 1)"
HASSURL="/api/${HASSAPIKEY}/states/sensor.yi_camera_motion_${CAMERA_NAME}"
BODY=$(cat <<EOF
{"state": "$STATE", "attributes": {"motion_file_name": "$FILENAME", "ip_address": "$IP_ADDRESS", "camera_name": "$CAMERA_NAME", "friendly_name": "$FRIENDLY_NAME"}}
EOF
)
BODY_LEN=$( busybox echo -n ${BODY} | wc -c )

busybox echo -ne "POST ${HASSURL} HTTP/1.0\r\nHost: ${HASSIP}\r\nContent-Type:application/json\r\nContent-Length: ${BODY_LEN}\r\n\r\n${BODY}" | nc -i 3 $HASSIP 80
