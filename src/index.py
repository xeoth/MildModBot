import praw
from os import getenv
import sqlite3
import logging
from datetime import timedelta, datetime
from sys import exit
from prawcore import NotFound
from praw.models import ModAction

reddit = praw.Reddit(
    client_id=getenv("MMB_CLIENT_ID"),
    client_secret=getenv("MMB_CLIENT_SECRET"),
    username=getenv("MMB_USERNAME"),
    password=getenv("MMB_PASSWORD"),
    user_agent="{}'s MildlyModBot".format(getenv("MMB_SUBREDDIT")),
)

logging.basicConfig(
    datefmt="%X %d.%m.%Y",
    format="[%(module)s] %(asctime)s | %(levelname)s: %(message)s",
    level=logging.INFO,
)


class DatabaseHelper:
    """Provides utilities for caching with SQLite"""

    def __init__(self):
        # will only be used for caching processed posts, the strikes will be saved as user flair
        self.cnx = sqlite3.connect(":memory:")
        self.cur = self.cnx.cursor()

        # initialize the schema
        self.cur.execute(
            """
        CREATE TABLE posts (
            post_id TEXT,
            date_added INTEGER
        );
        """
        )

    def add_post(self, post_id: str):
        self.cur.execute(
            "INSERT INTO posts VALUES (?, ?)",
            (post_id, int(datetime.utcnow().timestamp())),
        )
        self.cnx.commit()

    def check_post(self, post_id: str) -> bool:
        self.cur.execute("SELECT 0 FROM posts WHERE post_id=?", (post_id,))
        return bool(self.cur.fetchone())


def run():
    sub = reddit.subreddit(getenv('MMB_SUBREDDIT'))

    # listening for post flair edits
    for action in sub.mod.log(action='editflair'):
        # we only want flair changes on posts
        if not action.target_permalink:
            continue

        # first, we need to get the flair for a specified user


if __name__ == '__main__':
    if reddit.read_only:
        logging.critical('The reddit instance is read-only! Terminating...')
        exit(1)

    try:
        run()
    except NotFound:
        logging.fatal('The moderation log is not available to the signed in user. Are you using a mod account?')
        exit(1)
