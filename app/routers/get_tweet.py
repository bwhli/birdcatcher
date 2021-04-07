from fastapi import APIRouter
from ..util.Tweet import Tweet
from ..util.MintToken import MintToken

router = APIRouter()

@router.get("/get-tweet/")
async def get_tweet_route(tweet_url: str):
	tweet = Tweet(tweet_url)
	tweet_id = tweet.get_tweet_id()
	tweet_token = MintToken(tweet_id, None, None, None)
	tweet_uri_body = tweet_token.get_timestamped_tweet_body()
	return tweet_uri_body