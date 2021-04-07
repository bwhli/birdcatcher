# BirdCatcher

BirdCatcher is a Python API for timestamping tweets using ICON's IRC-31 token standard.

IRC-31 allows for multiple tokens to be minted with a single smart contract, wich each token being represented as a unique ID number. On Twitter, every tweet is represented by an ID number, which makes IRC-31 the perfect tool for the job – the tweet ID is the token ID.

BirdCatcher is currently in active development, but it is capable of doing the following:
1. Take a tweet URL as an input.
2. Parse the tweet ID, author's username, tweet body, and more.
3. Timestamp the IRC-31 JSON schema in an ICX transaction.
4. Mint an IRC-31 token with the JSON schema transaction hash as the URI.
5. Read timestamped metadata via the `/get-tweet/` endpoint.
