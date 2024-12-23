#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <pathname>"
  exit 1
fi

BASE_DIR="$1"

source $BASE_DIR/env/bin/activate
echo "Virtual ENV activated.."
sleep 0.3

python3 $BASE_DIR/crawler.py &
