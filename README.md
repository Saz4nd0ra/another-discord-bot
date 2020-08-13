## another-discord-bot

A bot made for servers that I like! 

## Running

You can setup your own instance of ADB, yet you should consider inviting the already hosted instance to your server. 
If you want to host it yourself, go ahead and read through the instructions.


## Installation

1. **Make sure to get Python 3.7 or higher, 3.8 is recommended.**

This is required to actually run the bot.

2. **Set up venv**

Just do `python3.8 -m venv adb`. If you don't have Python 3.8 installed, please Google instructions for your OS.

3. **Install dependencies**

To install the requirements do `pip3.8 install -U -r requirements.txt`.

4. **Setup configuration**

Change these settings in the `config/options.ini` to make the bot work. If the file doesn't exist, start the bot once to generate it. 

```ini
[Credentials]

Token = ...

[Audio]

LavalinkHost = ...
LavalinkPort = ...
LavalinkPassword = ...
```


## Requirements

- Python 3.7+
- discord.py
- wavelink

