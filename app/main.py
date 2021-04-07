from fastapi import FastAPI
from .routers import get_tweet, timestamp_tweet

app = FastAPI()

app.include_router(timestamp_tweet.router, prefix="/api/v1")
app.include_router(get_tweet.router, prefix="/api/v1")