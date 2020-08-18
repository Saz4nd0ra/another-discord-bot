#!/bin/bash

echo "This script is really basic! It won't close anything on its own so you will have to do it yourself when not using lavalink or the bot, kthxbye"

if java --version; then
     echo “Success, Java is installed.”
else
     echo “Failure, exit status: $?”
fi


echo "Starting lavalink server in screen lavalink"
screen -dmLS lavalink java -jar lavalink/Lavalink.jar

echo "Waiting 15 seconds to give lavalink enough time to start..."
sleep 5

echo "Checking for python venv"

venvdir="./venv/"
 
echo "Launching bot in screen adb"

screen -dmLS adb ./venv/bin/python run.py
 