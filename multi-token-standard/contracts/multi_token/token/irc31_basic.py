# Copyright 2021 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *

from .irc31_receiver import IRC31ReceiverInterface
from ..util import ZERO_ADDRESS, require
from ..util.rlp import rlp_encode_list

class IRC31Basic(IconScoreBase):

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        # id => (owner => balance)
        self._balances = DictDB('balances', db, value_type=int, depth=2)
        # owner => (operator => approved)
        self._operatorApproval = DictDB('approval', db, value_type=bool, depth=2)
        # id => token URI
        self._tokenURIs = DictDB('token_uri', db, value_type=str)
        # Store last minted token.
        self._lastTimestampedTweet = VarDB("last_timestamped_tweet", db, value_type=int)
        # Store token index (total number of tokens created).
        self._tokenIndex = VarDB("token_index", db, value_type=int)
        # ArrayDB for storing all IDs of timestamped tweets.
        self._timestampedTweets = ArrayDB('timestamped_tweets', db, value_type=int)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> int:
        return self._balances[_id][_owner]

    @external(readonly=True)
    def balanceOfBatch(self, _owners: List[Address], _ids: List[int]) -> List[int]:
        require(len(_owners) == len(_ids), "owner/id pairs mismatch")

        balances = []
        for i in range(len(_owners)):
            balances.append(self._balances[_ids[i]][_owners[i]])
        return balances

    @external(readonly=True)
    def tokenURI(self, _id: int) -> str:
        return self._tokenURIs[_id]

    @external(readonly=True)
    def timestampedTweets(self) -> list:
        l = self._tokenIndex.get()
        timestamped_tweets = [
            self._timestampedTweets.get(i) for i in range(l)
        ]
        return timestamped_tweets

    @external(readonly=True)
    def getLastTimestampedTweet(self):
        return self._lastTimestampedTweet.get()

    @external(readonly=True)
    def getTokenIndex(self):
        return self._tokenIndex.get()

    @external
    def transferFrom(self, _from: Address, _to: Address, _id: int, _value: int, _data: bytes = None):
        require(_to != ZERO_ADDRESS, "_to must be non-zero")
        require(_from == self.msg.sender or self.isApprovedForAll(_from, self.msg.sender),
                "Need operator approval for 3rd party transfers")
        require(0 <= _value <= self._balances[_id][_from], "Insufficient funds")

        # transfer funds
        self._balances[_id][_from] = self._balances[_id][_from] - _value
        self._balances[_id][_to] = self._balances[_id][_to] + _value

        # emit event
        self.TransferSingle(self.msg.sender, _from, _to, _id, _value)

        if _to.is_contract:
            # call `onIRC31Received` if the recipient is a contract
            recipient_score = self.create_interface_score(_to, IRC31ReceiverInterface)
            recipient_score.onIRC31Received(self.msg.sender, _from, _id, _value,
                                            b'' if _data is None else _data)

    @external
    def transferFromBatch(self, _from: Address, _to: Address, _ids: List[int], _values: List[int], _data: bytes = None):
        require(_to != ZERO_ADDRESS, "_to must be non-zero")
        require(len(_ids) == len(_values), "id/value pairs mismatch")
        require(_from == self.msg.sender or self.isApprovedForAll(_from, self.msg.sender),
                "Need operator approval for 3rd party transfers.")

        for i in range(len(_ids)):
            _id = _ids[i]
            _value = _values[i]
            require(0 <= _value <= self._balances[_id][_from], "Insufficient funds")

            # transfer funds
            self._balances[_id][_from] = self._balances[_id][_from] - _value
            self._balances[_id][_to] = self._balances[_id][_to] + _value

        # emit event
        self.TransferBatch(self.msg.sender, _from, _to, rlp_encode_list(_ids), rlp_encode_list(_values))

        if _to.is_contract:
            # call `onIRC31BatchReceived` if the recipient is a contract
            recipient_score = self.create_interface_score(_to, IRC31ReceiverInterface)
            recipient_score.onIRC31BatchReceived(self.msg.sender, _from, _ids, _values,
                                                 b'' if _data is None else _data)

    @external
    def setApprovalForAll(self, _operator: Address, _approved: bool):
        self._operatorApproval[self.msg.sender][_operator] = _approved
        self.ApprovalForAll(self.msg.sender, _operator, _approved)

    @external(readonly=True)
    def isApprovedForAll(self, _owner: Address, _operator: Address) -> bool:
        return self._operatorApproval[_owner][_operator]

    @eventlog(indexed=3)
    def TransferSingle(self, _operator: Address, _from: Address, _to: Address, _id: int, _value: int):
        pass

    @eventlog(indexed=3)
    def TransferBatch(self, _operator: Address, _from: Address, _to: Address, _ids: bytes, _values: bytes):
        """
        Must trigger on any successful token transfers, including zero value transfers as well as minting or burning.
        When minting/creating tokens, the `_from` must be set to zero address.
        When burning/destroying tokens, the `_to` must be set to zero address.

        :param _operator: the address of an account/contract that is approved to make the transfer
        :param _from: the address of the token holder whose balance is decreased
        :param _to: the address of the recipient whose balance is increased
        :param _ids: serialized bytes of list for token IDs (order and length must match `_values`)
        :param _values: serialized bytes of list for transfer amounts per token (order and length must match `_ids`)

        NOTE: RLP (Recursive Length Prefix) would be used for the serialized bytes to represent list type.
        """
        pass

    @eventlog(indexed=2)
    def ApprovalForAll(self, _owner: Address, _operator: Address, _approved: bool):
        """
        Must trigger on any successful approval (either enabled or disabled) for a third party/operator address
        to manage all tokens for the `_owner` address.

        :param _owner: the address of the token holder
        :param _operator: the address of authorized operator
        :param _approved: true if the operator is approved, false to revoke approval
        """
        pass

    @eventlog(indexed=1)
    def URI(self, _id: int, _value: str):
        pass

    # ===============================================================================================
    # Internal methods
    # ===============================================================================================

    def _mint(self, _owner: Address, _id: int, _supply: int, _uri: str, _username: str):
        self._balances[_id][_owner] = _supply

        # emit transfer event for Mint semantic
        self.TransferSingle(_owner, ZERO_ADDRESS, _owner, _id, _supply)

        # set token URI and emit event
        self._setTokenURI(_id, _uri)

        # Store token ID.
        self._storeTimestampedTweetId(_id)

        # Store last minted token.
        self._storeLastTimestampedTweet(_id)

        # Increment token index.
        self._incrementTokenIndex()

    def _burn(self, _owner: Address, _id: int, _amount: int):
        require(0 <= _amount <= self._balances[_id][_owner], "Not an owner or invalid amount")
        self._balances[_id][_owner] -= _amount

        # emit transfer event for Burn semantic
        self.TransferSingle(_owner, _owner, ZERO_ADDRESS, _id, _amount)

    def _setTokenURI(self, _id: int, _uri: str):
        self._tokenURIs[_id] = _uri
        self.URI(_id, _uri)

    def _storeTimestampedTweetId(self, _id: int):
        self._timestampedTweets.put(_id)

    def _storeLastTimestampedTweet(self, _id: int):
        self._lastTimestampedTweet.set(_id)

    def _incrementTokenIndex(self):
        self._tokenIndex.set(self._tokenIndex.get() + 1)
