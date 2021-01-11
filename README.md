# MildModBot

A bot providing an efficient way to execute r/MildlyInteresting's [preventive restriction policy](https://www.reddit.com/r/mildlyinteresting/wiki/index#wiki_moderation_policy).

So, how does this policy work? You can learn everything from the link above, but TL;DR for every time mods remove your post, you get one strike. Three strikes, and you're banned\*

\* The bot does not ban the user, but sends you a modmail every time a user reaches three strikes.

## Setup

To set up the bot, you'll need a client ID and a client secret. Get those by making a script-type app at https://reddit.com/prefs/apps

### Windows

1. Right-click on Start and click "Windows Powershell"
2. Declare a few environmental variables using these commands:

```powershell
$env:MMB_CLIENT_ID="your client ID"
$env:MMB_CLIENT_SECRET="your client secret"
$env:MMB_USERNAME="your bot's username"
$env:MMB_PASSWORD="your bot's password"
$env:MMB_SUBREDDIT="your subreddit"
```

3. Clone the repo via `git clone https://github.com/Xeoth/MildModBot.git` (you may need to [install git](https://git-scm.com/downloads) first; if you don't want to install it, [download the code as ZIP](https://github.com/Xeoth/MildModBot/archive/master.zip) and unpack it).
4. `cd` into the newly created MildModBot folder
5. Use `py -m venv venv` to create a virtual environment, and activate it via `.\venv\Scripts\activate.ps1` (you may need to [install Python](https://www.python.org/downloads/) first)
6. Use `pip3 install -r requirements.txt` to install bot's dependencies
7. Finally, use `py src\index.py` to run the bot.

If you did everything right, you will get a message saying "INFO: The bot is running."

### Linux

1. Launch a terminal. Or, if your entire system is just a terminal, don't do anything.
2. Declare a few environmental variables using this command:

```sh
export MMB_CLIENT_ID="your client ID" \
       MMB_CLIENT_SECRET="your client secret" \
       MMB_USERNAME="your bot's username" \
       MMB_PASSWORD="your bot's password" \
       MMB_SUBREDDIT="your subreddit"
```
3. Clone the repo via `git clone https://github.com/Xeoth/MildModBot.git` (you may need to [install git](https://git-scm.com/downloads) first; if you don't want to install it, [download the code as ZIP](https://github.com/Xeoth/MildModBot/archive/master.zip) and unpack it).
4. `cd` into the newly created MildModBot folder
5. Use `python3 -m venv venv` to create a virtual environment, and activate it via `./venv/bin/activate`. (you may need to [install Python](https://www.python.org/downloads/) first)
6. Use `pip3 install -r requirements.txt` to install bot's dependencies
7. Finally, use `python3 src/index.py` to run the bot.

If you did everything right, you will get a message saying "INFO: The bot is running."
