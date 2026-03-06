import instaloader

def fetch_public_profile(username: str):

    L = instaloader.Instaloader()

    profile = instaloader.Profile.from_username(L.context, username)

    followers = profile.followers
    following = profile.followees
    posts = profile.mediacount

    total_likes = 0
    total_comments = 0
    count = 0

    # fetch last 12 posts
    for post in profile.get_posts():

        total_likes += post.likes
        total_comments += post.comments

        count += 1
        if count == 12:
            break

    avg_likes = total_likes // count if count else 0
    avg_comments = total_comments // count if count else 0

    return {
        "username": username,
        "followers": followers,
        "following": following,
        "total_posts": posts,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "avg_reel_views": 0
    }