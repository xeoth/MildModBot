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
        self.cnx = sqlite3.connect("posts.db")
        self.cur = self.cnx.cursor()

        # initialize the schema
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS posts (
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
    log_stream = sub.mod.stream.log(action="editflair")
    for action in log_stream:
        """
        'description': None, 'target_body': None, 'mod_id36': 'v16iabx', 'created_utc': 1604159047.0, 'subreddit': 'xeothtest', 'target_title': 'ps 3', 'target_permalink': '/r/xeothtest/comments/hhz1a4/ps_3/', 'subreddit_name_prefixed': 'r/xeothtest', 'details': 'flair_edit', 'action': 'editflair', 'target_author': 'alteoth', 'target_fullname': 't3_hhz1a4', 'sr_id36': '2i4bah', 'id': 'ModAction_e9427abc-1b8f-11eb-91ee-9e594cb2ce46', '_mod': 'Xeoth'}b
        """
        # we only want flair changes on posts
        if not action.target_permalink:
            continue

        # first, we need to get the flair for a specified user
        # we're fetching one but it's still not subscriptable, hence the loop
        for f in sub.flair(redditor=action.target_author):
            flair = f

        flair_class = flair["flair_css_class"]
        submission = reddit.submission(action.target_fullname[3:])
        post_id = submission.id

        # checking whether the post was already processed
        if db.check_post(post_id) or post_id in flair:
            logging.debug(f"{post_id} already processed; continuing.")
            continue

        if not flair_class:
            logging.info(f"{post_id}'s author, {flair['user']}, did not have a flair, so assigning one.")
            sub.flair.set(redditor=flair["user"], css_class=f"1s {post_id}")
            db.add_post(post_id)
            continue

        # the format of the flair_css_class will look like Xs AAAAA BBBBB CCCCC
        # here, we need just the X
        strikes_amount = int(flair_class.split(' ')[0][0]) + 1

        new_flair = f"{strikes_amount}s {flair['flair_css_class'][3:]} {post_id}"

        sub.flair.set(redditor=flair["user"], css_class=new_flair)
        db.add_post(post_id)

        logging.info(f"{flair['user']} now at {strikes_amount} strikes.")

        # checking whether the user deserves a ban
        if strikes_amount >= 3:
            message = f"""
/r/{sub.display_name}/about/banned
            
    Greetings u/{flair["user"]}, you have been banned for reaching three strikes as per our [moderation policy](https://reddit.com/r/mildlyinteresting/wiki/index#wiki_moderation_policy).
                    
    Your strikes are:
    """

            # adding the actual strikes to the message
            for strike in new_flair.split(' ')[1:]:  # we don't want the 'Xs' part
                message += f"\n    - /r/{sub.display_name}/comments/{strike}"

            sub.message(
                subject="A user has reached three strikes!",
                message=message
            )

            logging.info(f"Message about {flair['user']} sent.")


if __name__ == "__main__":
    if reddit.read_only:
        logging.critical("The reddit instance is read-only! Terminating...")
        exit(1)

    try:
        logging.info('The bot is running.')
        run()
    except NotFound:
        logging.fatal(
            "The moderation log is not available to the signed in user. Are you using a mod account?"
        )
        exit(1)
