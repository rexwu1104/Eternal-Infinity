#!/bin/bash

set -e

trap 'kill $(jobs -p); exit 1' TERM
trap 'kill $(jobs -p); exit 2' INT

rm -f input && mkfifo input

youtube-dl --no-playlist "$1" -o - > input &

ffmpeg -re -i input -vf 'scale=1280:720,fps=30' -pix_fmt rgb24 -f v4l2 /dev/video0 -f alsa -ac 2 -ar 48000 -c:a pcm_s32le hw:0,1,0 &

wait $!