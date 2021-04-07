from io import BytesIO
from PIL import Image
import base64
import json
import re
import requests

class Tweet:
	def __init__(self, tweet_url):
		self.tweet_url = tweet_url

	def get_tweet_id(self) -> str:
		tweet_id = re.findall(r"[http?s//]?twitter\.com\/.*\/status\/(\d+)", self.tweet_url)[0]
		return tweet_id

	def get_tweet_user(self) -> str:
		tweet_user = re.findall(r"[http?s//]?twitter\.com\/(.*)\/status\/\d+", self.tweet_url)[0]
		return tweet_user

	def get_tweet_body(self) -> str:
		if self.is_valid_tweet() == True:
			tweet_id = self.get_tweet_id()
			api_endpoint = f"https://api.twitter.com/2/tweets?ids={tweet_id}&tweet.fields=author_id,conversation_id,created_at,source"
			request_headers = { "Authorization": "Bearer" }
			response = requests.get(api_endpoint, headers=request_headers, timeout=5).json()["data"][0]
			return json.dumps(response, ensure_ascii=False, sort_keys=True)
		else:
			return "Tweet ID is invalid."

	def generate_tweet_image_url(self):
		tweet_id = self.get_tweet_id()
		headers = {
			'Content-Type': 'application/json',
			'Authorization': '',
		}
		data = { "tweetId": str(tweet_id) }
		response = requests.post('https://tweetpik.com/api/images', headers=headers, data=json.dumps(data)).json()
		image_url = response["url"]
		return image_url

	def generate_tweet_image_b64_string(self):
		image_url = self.generate_tweet_image_url()
		response = requests.get(image_url, stream=True)
		response.raw.decode_content = True
		image = Image.open(response.raw)
		buffered = BytesIO()
		image.save(buffered, format="PNG", optimize=True)
		tweet_image_b64_string = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
		return tweet_image_b64_string

	def is_valid_tweet(self) -> bool:
		tweet_id = self.get_tweet_id()
		api_endpoint = f"https://api.twitter.com/2/tweets?ids={tweet_id}"
		request_headers = { "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAAPPFOAEAAAAApclDFCXIO%2BfFbl15yS%2BbMlcp6nY%3DcaqujqfBPbr2Tsld3BbYCRRYDYoJhC7IhcM0fPl4pYUgtbvnux" }
		response = requests.get(api_endpoint, headers=request_headers, timeout=5).json()
		if "errors" in response:
			return False
		else:
			return True
