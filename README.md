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


4. **Create the database in PostgreSQL**

You will need PostgreSQL 9.5. First, initialize Postgres with a series of commands

```
sudo su postgres -l
initdb --locale $LANG -E UTF8 -D '/var/lib/postgres/data/'
```

The second command has different options, like locales and location, change them to your liking, or use the defaults. After staring the postgres service use the `psql` tool and use the following commands to create a new database.

```sql
CREATE ROLE adb WITH LOGIN PASSWORD 'samplepassword';
CREATE DATABASE adb OWNER adb;
CREATE EXTENSION pg_trgm;
```

5. **Setup configuration**

Change these settings in the `config/options.ini` to make the bot work. If the file doesn't exist, start the bot once to generate it. 

```ini
[Credentials]

Token = ...

[Audio]

LavalinkHost = ...
LavalinkPort = ...
LavalinkPassword = ...

[Postgres]

Path = postgresql://adb:samplepassword@127.0.0.1/adb
```

6. **Configuration of database**

To configure the PostgreSQL database for use by the bot, go to the directory where `launcher.py` is located, and run the script by doing `python3.8 launcher.py db init`

## Requirements

- Python 3.7+
- discord.py
- wavelink
- and many more to come

