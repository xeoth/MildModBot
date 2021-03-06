# MildModBot

A bot providing an efficient way to execute r/MildlyInteresting's [preventive restriction policy](https://www.reddit.com/r/mildlyinteresting/wiki/index#wiki_moderation_policy).

So, how does this policy work? You can learn everything from the link above, but TL;DR for every time mods remove your post, you get one strike. Three strikes, and you're banned\*

\* The bot does not ban the user, but sends you a modmail every time a user reaches three strikes.

## Setup

To set up the bot, you'll need a client ID and a client secret. Get those by making a script-type app at https://reddit.com/prefs/apps

## Using Docker

This is the recommended route, as it's much more straightforward and requires less technical skills.

For this path, you will need to [install Docker](https://www.docker.com/products/docker-desktop).

1. Use `docker pull xeoth/mildmodbot` to pull the image.
2. Create an `env.txt` file and put the following content inside:

```env
MMB_USERNAME=your_bot_username
MMB_PASSWORD=your_bot_password
MMB_CLIENT_ID=your_bot_client_id
MMB_CLIENT_SECRET=your_bot_client_secret
MMB_SUBREDDIT=mildlyinteresting
```

3. Run the image with `docker run --env-file ./env.txt --restart unless-stopped --detach xeoth/mildmodbot` (of course replacing `./env.txt` with the actual path to that file).

You should see an ID printed out. To see whether it works, use `docker ps` and check if "Up X seconds" is the status of xeoth/mildmodbot. If so, it should be up and running. Check you sub's modlog to see whether it's assigning flairs.

You can view the logs using `docker logs [container ID here]` or with the desktop app.

## Manually

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
