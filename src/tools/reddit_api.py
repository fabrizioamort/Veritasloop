# reddit_api.py
import os
import praw

def search_reddit(query: str, subreddits: list[str]) -> list[dict]:
    """
    Searches for reddit posts using the PRAW library.

    Args:
        query (str): The search query.
        subreddits (list[str]): A list of subreddits to search in.

    Returns:
        list[dict]: A list of reddit posts.
    """
    try:
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent="veritasloop by u/yourusername",
        )

        results = []
        for subreddit_name in subreddits:
            subreddit = reddit.subreddit(subreddit_name)
            for submission in subreddit.search(query, sort="relevance", time_filter="all"):
                submission.comments.replace_more(limit=0)
                comments = []
                for comment in submission.comments.list()[:5]:  # Get top 5 comments
                    comments.append({
                        "body": comment.body,
                        "author": str(comment.author),
                        "score": comment.score
                    })

                results.append({
                    "title": submission.title,
                    "url": submission.url,
                    "score": submission.score,
                    "selftext": submission.selftext,
                    "comments": comments
                })
        return results
    except Exception as e:
        print(f"Error searching reddit: {e}")
        return []
