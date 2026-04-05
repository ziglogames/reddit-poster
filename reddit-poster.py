"""
Reddit Scheduled Poster
=======================
Posts to Reddit on a timed schedule from a JSON config file.

Setup:
  1. Go to https://www.reddit.com/prefs/apps and create a "script" app
  2. Copy your client_id (under the app name) and client_secret
  3. Install PRAW:  pip install praw
  4. Fill in your credentials below (or use environment variables)
  5. Edit posts.json with your posts
  6. Run:  python reddit_scheduler.py
"""

import praw
import json
import time
import os
import sys
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────
# You can set these directly or use environment variables.

REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDDIT_USERNAME      = os.getenv("REDDIT_USERNAME", "YOUR_USERNAME")
REDDIT_PASSWORD      = os.getenv("REDDIT_PASSWORD", "YOUR_PASSWORD")
REDDIT_USER_AGENT    = "game-promo-scheduler/1.0 (by /u/YOUR_USERNAME)"

POSTS_FILE           = "posts.json"       # Path to your posts config
DELAY_SECONDS        = 36000              # 36000 = 10 hours between posts

# ── Reddit Client ─────────────────────────────────────────────────

def create_reddit_client():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT,
    )
    # Verify login
    print(f"Logged in as: {reddit.user.me()}")
    return reddit


# ── Load Posts ────────────────────────────────────────────────────

def load_posts(filepath):
    with open(filepath, "r") as f:
        posts = json.load(f)

    print(f"Loaded {len(posts)} posts from {filepath}\n")
    for i, post in enumerate(posts):
        print(f"  [{i+1}] r/{post['subreddit']} — {post['title'][:60]}")
    print()

    return posts


# ── Submit a Single Post ──────────────────────────────────────────

def submit_post(reddit, post):
    subreddit = reddit.subreddit(post["subreddit"])
    post_type = post.get("type", "link")  # "link", "image", or "text"
    title = post["title"]

    if post_type == "image":
        # Upload an image from a local file path
        submission = subreddit.submit_image(
            title=title,
            image_path=post["image_path"],
            flair_id=post.get("flair_id"),
        )
    elif post_type == "text":
        submission = subreddit.submit(
            title=title,
            selftext=post.get("body", ""),
            flair_id=post.get("flair_id"),
        )
    else:
        # Default: link post (works for gifs, videos, URLs)
        submission = subreddit.submit(
            title=title,
            url=post["url"],
            flair_id=post.get("flair_id"),
        )

    return submission


# ── Main Scheduler Loop ──────────────────────────────────────────

def run_scheduler():
    reddit = create_reddit_client()
    posts = load_posts(POSTS_FILE)

    total = len(posts)

    for i, post in enumerate(posts):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Posting {i+1}/{total}: r/{post['subreddit']} — {post['title'][:60]}")

        try:
            submission = submit_post(reddit, post)
            print(f"  ✓ Success! {submission.shortlink}\n")
        except praw.exceptions.RedditAPIException as e:
            print(f"  ✗ Reddit API error: {e}\n")
        except Exception as e:
            print(f"  ✗ Error: {e}\n")

        # Wait before next post (skip wait after the last one)
        if i < total - 1:
            next_time = datetime.now().strftime("%H:%M:%S")
            print(f"  Waiting {DELAY_SECONDS // 60} minutes until next post...")
            time.sleep(DELAY_SECONDS)

    print("All posts submitted!")


if __name__ == "__main__":
    run_scheduler()
