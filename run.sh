#!/bin/bash

cd "$(dirname "$BASH_SOURCE")"

nohup java -jar lavalink/Lavalink.jar &

adb/bin/python launcher.py &

