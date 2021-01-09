import praw
from os import getenv
import sqlite3
import logging
from datetime import timedelta, datetime
from sys import exit
from prawcore import NotFound

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
    sub = reddit.subreddit(getenv("MMB_SUBREDDIT"))
    db = DatabaseHelper()

    # listening for post flair edits
    for action in sub.mod.log(action="editflair"):
        """
        'description': None, 'target_body': None, 'mod_id36': 'v16iabx', 'created_utc': 1604159047.0, 'subreddit': 'xeothtest', 'target_title': 'ps 3', 'target_permalink': '/r/xeothtest/comments/hhz1a4/ps_3/', 'subreddit_name_prefixed': 'r/xeothtest', 'details': 'flair_edit', 'action': 'editflair', 'target_author': 'alteoth', 'target_fullname': 't3_hhz1a4', 'sr_id36': '2i4bah', 'id': 'ModAction_e9427abc-1b8f-11eb-91ee-9e594cb2ce46', '_mod': 'Xeoth'}b
        """
        # we only want flair changes on posts
        if not action.target_permalink:
            continue

        # first, we need to get the flair for a specified user
        # we're fetching one but it's still not subscriptable
        for f in sub.flair(redditor=action.target_author):
            flair = f

        flair_class = flair.flair_css_class
        if not flair_class:
            sub.mod.flair.set(redditor=flair.user, css_class=f"1s {flair.target_fullname[3:]}")
            db.add_post(flair.target_fullname[3:])
            continue

        # the format of the flair_css_class will look like Xs AAAAA BBBBB CCCCC
        # here, we need just the X
        strikes_amount = int(flair.css_class.split(' ')[0][0]) + 1

        new_flair = f"{strikes_amount} {flair.css_class[3:]}"

        sub.mod.flair.set(redditor=flair.user, css_class=new_flair)
        db.add_post(flair.target_fullname[3:])


if __name__ == "__main__":
    if reddit.read_only:
        logging.critical("The reddit instance is read-only! Terminating...")
        exit(1)

    try:
        run()
    except NotFound:
        logging.fatal(
            "The moderation log is not available to the signed in user. Are you using a mod account?"
        )
        exit(1)
