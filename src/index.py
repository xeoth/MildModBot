import praw
from praw import models
import sys
from os import getenv
import sqlite3
import logging
from prawcore import NotFound

reddit = praw.Reddit(
    client_id=getenv("MMB_CLIENT_ID"),
    client_secret=getenv("MMB_CLIENT_SECRET"),
    username=getenv("MMB_USERNAME"),
    password=getenv("MMB_PASSWORD"),
    user_agent=f"{getenv('MMB_SUBREDDIT')}'s MildModBot",
)

logging.basicConfig(
    datefmt="%X %d.%m.%Y",
    format="[%(module)s] %(asctime)s | %(levelname)s: %(message)s",
    level=logging.INFO,
)

SPAMBOT_MESSAGE = """
## Attention!

u/{} is a reposting bot. Users like them are not real. They're automated bots meant to gain karma and then sell the account.

Common behavior for these bots is making posts after a long period of inactivity to avoid detection by systems that filter out posts made by new accounts.

This account has been banned, but there are more like it. Please help us get rid of them by reporting them to us. They ruin the fun for everyone, as the community gets less fresh content.
"""


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
        submission: models.Submission = reddit.submission(action.target_fullname[3:])
        post_id = submission.id

        # checking whether the post was already processed
        if flair_class is not None and (db.check_post(post_id) or post_id in flair_class):
            logging.debug(f"{post_id} already processed; continuing.")
            continue

        if submission and submission.link_flair_text and "Spam Bot" in submission.link_flair_text and \
                submission.author is not None and submission.author.name: 
            # we're dealing with a spam bot. ban and leave a comment explaining the thing.
            logging.info(f"{post_id}'s OP was determined to be a spambot, so they'll be banned.")
            try:
                sub.banned.add(submission.author.name)
            except NameError:
                pass
            # check if already removed to avoid double modlogs
            if not submission.removed_by_category:
                submission.mod.remove()
            submission.reply(SPAMBOT_MESSAGE.format(submission.author.name)).mod.distinguish(how="yes", sticky=True)
            db.add_post(submission.id)
            continue
        elif submission.link_flair_text is not None and "Removed:" not in submission.link_flair_text:
            # we don't want to assign strikes for 'overdone' and 'quality post' flairs
            logging.info(f"{post_id} was flaired, but not removed; continuing")
            continue
            
        if not submission.removed_by_category:
            submission.mod.remove()

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
            # composing the message
            message = f"/r/{sub.display_name}/about/banned\n\n^| "
            # [1:] because we don't want the '2s' part, only the IDs
            strikes = new_flair.split(" ")[1:]

            # adding quick links to posts
            for strike in strikes:
                message += f"[^({strike})](https://redd.it/{strike} \"View post with ID {strike}\") ^| "

            # adding the actual content
            message += f"""\n\n
    Greetings u/{flair["user"]}, you have been banned for reaching three strikes as per our [moderation policy](https://reddit.com/r/mildlyinteresting/wiki/index#wiki_moderation_policy).
                    
    Your strikes are:
    """

            # adding the actual strikes to the message
            for strike in strikes:
                message += f"\n    - /r/{sub.display_name}/comments/{strike}"
            
            message += "\n\nHowever, your ban can be rescinded 30 days after you were banned via the process outlined in our moderation policy, [accessible here](https://www.reddit.com/r/mildlyinteresting/wiki/index#wiki_lifting_a_restriction)."

            sub.message(subject="[Notification] A user has reached three strikes!",
                        message=message)

            logging.info(f"Message about {flair['user']} sent.")


if __name__ == "__main__":
    if reddit.read_only:
        logging.critical("The reddit instance is read-only! Terminating...")
        sys.exit(1)

    try:
        logging.info("The bot is running.")
        run()
    except NotFound:
        logging.fatal(
            "The moderation log is not available to the signed in user. Are you using a mod account?"
        )
        sys.exit(1)
