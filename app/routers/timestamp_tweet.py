from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..util.Tweet import Tweet
from ..util.MintToken import MintToken

router = APIRouter()

class TweetRequest(BaseModel):
	tweet_url: str

@router.post("/timestamp-tweet/")
async def timestamp_tweet(tweet_url: TweetRequest):
	tweet = Tweet(tweet_url.tweet_url)
	tweet_id = tweet.get_tweet_id()
	if is_token_minted(tweet_id) == False:
		tweet_user, tweet_body, tweet_image = tweet.get_tweet_user(), tweet.get_tweet_body(), tweet.generate_tweet_image_b64_string()
		tweet_token = MintToken(tweet_id, tweet_user, tweet_body, tweet_image)
		return tweet_token.mint_tweet_token()
	else:
		raise HTTPException(status_code=500, detail=f"Token ID# {tweet_id} has already been minted.")