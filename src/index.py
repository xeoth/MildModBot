import praw
from os import getenv
import sqlite3
import logging
from sys import exit
from prawcore import NotFound

reddit = praw.Reddit(
    client_id=getenv("MMB_CLIENT_ID"),
    client_secret=getenv("MMB_CLIENT_SECRET"),
    username=getenv("MMB_USERNAME"),
    password=getenv("MMB_PASSWORD"),
    user_agent="{}'s MildModBot".format(getenv("MMB_SUBREDDIT")),
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
            "INSERT INTO posts VALUES (?, strftime('%s', 'now'))", (post_id,)
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

        # we don't want to assign strikes for 'overdone' and 'quality post' flairs
        if "Removed:" not in submission.link_flair_text:
            logging.info(f"{post_id} was flaired, but not removed; continuing")
            continue

        # first time offenders do not have any class
        if not flair_class:
            logging.info(
                f"{post_id}'s author, {flair['user']}, did not have a flair, so assigning one."
            )
    
            sub.flair.set(redditor=flair["user"], css_class=f"1s {post_id}")
            db.add_post(post_id)
            continue

        # the flair will look somewhat like '2s ndue43 aqsnz', and we need to get the strike count (the first character)
        strikes_amount = int(flair_class[0]) + 1

        # constructing and setting the new which includes the incremented strike count, and the new post ID
        new_flair = f"{strikes_amount}s {flair['flair_css_class'][3:]} {post_id}"
        sub.flair.set(redditor=flair["user"], css_class=new_flair)

        # saving in the DB
        db.add_post(post_id)

        logging.info(
            f"{flair['user']} is now at {strikes_amount} strikes (last post removed: {post_id})."
        )

        # checking whether the user deserves a ban
        if strikes_amount >= 3:
            message = f"""
/r/{sub.display_name}/about/banned
            
    Greetings u/{flair["user"]}, you have been banned for reaching three strikes as per our [moderation policy](https://reddit.com/r/mildlyinteresting/wiki/index#wiki_moderation_policy).
                    
    Your strikes are:
    """
    
            # adding the actual strikes to the message
            # fmt: off
            for strike in new_flair.split(" ")[1:]:  # [1:] because we don't want the '2s' part, only the IDs
                message += f"\n    - /r/{sub.display_name}/comments/{strike}"
            # fmt: on
    
            sub.message(subject="A user has reached three strikes!", message=message)
    
            logging.info(f"Message about {flair['user']} sent.")


if __name__ == "__main__":
    if reddit.read_only:
        logging.critical("The reddit instance is read-only! Terminating...")
        exit(1)

    try:
        logging.info("The bot is running.")
        run()
    except NotFound:
        logging.fatal(
            "The moderation log is not available to the signed in user. Are you using a mod account?"
        )
        exit(1)
