# another-discord-bot

A bot made for servers that I like! 

### Before we start

You can setup your own instance of ADB, yet you should consider inviting the already hosted instance to your server. 
If you want to host it yourself, go ahead and read through the instructions.


## Installation

These are the instructions to install Lavalink and the bot itself. The bot is written with Linux in mind,
so Windows support isn't confirmed. Any major distro should work, these instructions are written using Arch.

### Installation: Lavalink

1. **Install Java 11.**

Please look this up, since that process is different for each modern OS. 

### Installation: Python

1. **Checking the version of Python**

Some distros come with Python 3.7 or 3.8 preinstalled. You can check the version with either `python --version` or `python3 --version`.
If one of the commands gave the output or `Python 3.7.x` or `Python 3.8.x` you can skip the installation of Python.

2. **Installing Python**

Again, look this up on the internet.

### Installation: Venv and dependencies

1. **Set up a virtual environment.**

Just do `python3 -m venv venv`. If things don't work, please look up the error messages, and use the internet. 

2. **Install dependencies**

first you need to activate the venv with `source /venv/bin/activate`.
You are now using the venv, well done. You might need to install wheel using `pip install wheel`,
after that is finished, install the requirements with `pip install -r requirements.txt`, this could take a while.

You finished with the installation, now you can go ahead and set everything up.

## Setup

### Bot configuration

**Setup configuration**

Change these settings in the `config/options.ini` to make the bot work. If the file doesn't exist, start the bot once to generate it.

```ini
[Credentials]

Token = ...

[Audio]

LavalinkHost = ...
LavalinkPort = ...
LavalinkPassword = ...
```

## Other stuff

TODO
