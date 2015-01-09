#!/bin/bash
#
# Upload videos to youtube using youtube-upload and curl.
#
#   $ youtube-upload --get-upload-form-info ... | upload_with_curl.sh [CURL_OPTIONS]
#
set -e

debug() { echo "$@" >&2; }

while { read FILE; read TOKEN; read POST_URL; }; do
  URL="$POST_URL?nexturl=http://code.google.com/p/youtube-upload"
  VIDEO_ID=$(curl --include -F "token=$TOKEN" -F "file=@$FILE" "$@" "$URL" | 
    grep -m1 "^Location: " | grep -o "id=[^&]\+" | cut -d"=" -f2-)
  test "$VIDEO_ID" || { debug "Error uploading"; exit 1; }            
  echo "http://www.youtube.com/watch?v=$VIDEO_ID"
done
