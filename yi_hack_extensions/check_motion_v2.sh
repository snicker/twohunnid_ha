#!/bin/sh
echo "monitoring started for $CAMERA_NAME ($FRIENDLY_NAME)"
previous_state=1
current_state=0
previous_motion_file="null"
while [ 1 ]
do
  last_hour=$(TZ=$(printf "UTC%02d00" $((`expr "$(date +%z)" "*" "-1"` / 100 + 1))) date '+%YY%mM%dD%HH')
  this_hour=$(date '+%YY%mM%dD%HH')
  motion_file=$(find /home/hd1/record/$last_hour/ /home/hd1/record/$this_hour/ -type f -name "*.mp4" -mmin -1 2>/dev/null | tail -1)
  tmp_motion_file=$(find /home/hd1/record/$last_hour/ /home/hd1/record/$this_hour/ -type f -name "*.tmp" -mmin -1 2>/dev/null | tail -1)
  echo $motion_file | sed "s/.\//record\//" > /home/hd1/test/http/motion

  filename_len=$(( ${#tmp_motion_file} + ${#motion_file} ))
  if [ $(( $filename_len + 0 )) -gt 0 ]
  then
    current_state=1
  else
    current_state=0
  fi
  if [ ${#motion_file} -gt 0 ]
  then
    motion_file=$motion_file 
  else
    motion_file="null"
  fi
  if [ $current_state != $previous_state ] || [ $motion_file != $previous_motion_file ]
  then
    echo "motion state change: $current_state file: $motion_file"
    ./hass_motion.sh "$CAMERA_NAME" "$FRIENDLY_NAME" "$current_state" "$motion_file" > ./hass_motion.log &
    previous_state=$current_state
    previous_motion_file=$motion_file
  fi
  sleep 3 
done
