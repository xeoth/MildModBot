import praw
from os import getenv
import sqlite3

reddit = praw.Reddit(
    client_id=getenv("MMB_CLIENT_ID"),
    client_secret=getenv("MMB_CLIENT_SECRET"),
    username=getenv("MMB_USERNAME"),
    password=getenv("MMB_PASSWORD"),
    user_agent="{}'s MildlyModBot".format(getenv("MMB_SUBREDDIT")),
)


class DatabaseHelper:
    """Provides utilities for caching with SQLite"""

    def __init__(self):
        # will only be used for caching processed posts, the strikes will be saved as user flair
        self.cnx = sqlite3.connect(":memory:")
        self.cur = self.cnx.cursor()

        # initialize the schema
        self.cur.execute('''
        CREATE TABLE posts (
            post_id TEXT
        );
        ''')

    def add_post(self, post_id: str):
        self.cur.execute('INSERT INTO posts VALUES (?)', (post_id,))
        self.cnx.commit()

    def check_post(self, post_id: str) -> bool:
        self.cur.execute('SELECT 0 FROM posts WHERE post_id=?', (post_id,))
        return bool(self.cur.fetchone())


def run():
    pass
