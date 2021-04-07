import base64
import json
import requests
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import (
    CallTransactionBuilder,
    MessageTransactionBuilder
)
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet

wallet = KeyWallet.load("keystore", "password123~~")
icx_api_endpoint = "http://localhost:9000/api/v3"
icon_service = IconService(HTTPProvider("http://localhost:9000", 3))
irc31_contract_address = "cx7bf6fc3501bc9478b822d197249fb03f1bf32c2f"

class MintToken:

	def __init__(self, tweet_id, tweet_user, tweet_body, tweet_image):
		self.tweet_id = tweet_id
		self.tweet_user = tweet_user
		self.tweet_body = tweet_body
		self.tweet_image = tweet_image

	def get_tweet_uri(self):
		params = {
			"_id": self.tweet_id
		}
		call = CallBuilder()\
			.from_(wallet.get_address())\
			.to(irc31_contract_address)\
			.method("tokenURI")\
			.params(params)\
			.build()
		result = icon_service.call(call)
		return result

	def get_timestamped_tweet_body(self):
		token_uri = self.get_tweet_uri()
		json_rpc_payload = {
		    "jsonrpc": "2.0",
		    "method": "icx_getTransactionByHash",
		    "id": 1234,
		    "params": {
		        "txHash": token_uri
		    }
		}
		icx_get_transaction_by_hash_request = requests.post(icx_api_endpoint, json=json_rpc_payload)
		icx_get_transaction_by_hash_request_json = json.loads(icx_get_transaction_by_hash_request.text)
		icx_transaction_data_hex = icx_get_transaction_by_hash_request_json["result"]["data"][2:]
		icx_transaction_data = bytes.fromhex(icx_transaction_data_hex).decode("utf-8")
		return json.loads(icx_transaction_data)

	def prepare_tweet_body(self):
		prepared_tweet_body = {}
		tweet_body = json.loads(self.tweet_body)
		prepared_tweet_body["name"] = self.tweet_id
		prepared_tweet_body["description"] = f"A timestamped tweet by @{self.tweet_user} – https://twitter.com/{self.tweet_user}/status/{self.tweet_id}."
		prepared_tweet_body["image"] = self.tweet_image
		prepared_tweet_body["properties"] = tweet_body
		return json.dumps(prepared_tweet_body)

	def timestamp_tweet_body(self):
		prepared_tweet_body = self.prepare_tweet_body()
		tweet_body_hex = prepared_tweet_body.encode("utf-8").hex()
		transaction = MessageTransactionBuilder()\
			.from_(wallet.get_address())\
			.to(wallet.get_address())\
			.data(f"0x{tweet_body_hex}")\
			.nid(3)\
			.build()
		estimate_step = icon_service.estimate_step(transaction)
		step_limit = estimate_step + 10000
		signed_transaction = SignedTransaction(transaction, wallet, step_limit)
		tx_hash = icon_service.send_transaction(signed_transaction)
		self.check_tx_result(tx_hash)
		return tx_hash

	def mint_tweet_token(self):
		token_uri = self.timestamp_tweet_body()
		params = {
			"_id": self.tweet_id,
			"_supply": 1,
			"_uri": token_uri,
			"_username": self.tweet_user
		}
		transaction = CallTransactionBuilder()\
			.from_(wallet.get_address())\
			.to(irc31_contract_address) \
			.nid(3) \
			.nonce(100) \
			.method("mint")\
			.params(params)\
			.build()
		estimate_step = icon_service.estimate_step(transaction)
		step_limit = estimate_step + 10000
		signed_transaction = SignedTransaction(transaction, wallet, step_limit)
		tx_hash = icon_service.send_transaction(signed_transaction)
		self.check_tx_result(tx_hash)
		response = {
			"mint_tx_hash": tx_hash,
			"mint_params": {
				"_id": self.tweet_id,
				"_uri": token_uri,
				"_username": self.tweet_user,
				"_supply": 1
			}
		}
		return response

	def check_tx_result(self, tx_hash: str):
		while True:
			try:
				tx_result = icon_service.get_transaction_result(tx_hash)
				if tx_result["status"] == 1:
					break
			except:
				continue
		return tx_result["eventLogs"]

def is_token_minted(tweet_id):
		params = {
			"_id": tweet_id
		}
		call = CallBuilder()\
			.from_(wallet.get_address())\
			.to(irc31_contract_address)\
			.method("tokenURI")\
			.params(params)\
			.build()
		result = icon_service.call(call)
		if len(result) > 0:
			return True
		else:
			return False