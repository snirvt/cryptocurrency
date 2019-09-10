from functools import reduce
import hashlib as hl

import json
import pickle
import requests

# Import two functions from our hash_util.py file. Omit the ".py" in the import
from utility.hash_util import hash_block
from utility.verification import Verification
from utility.broadcast import broadcast_transaction
from utility.broadcast import broadcast_block
from utility.broadcast import broadcast_chain
from utility.broadcast import broadcast_open_transactions
from utility.broadcast import broadcast_chain_all_nodes
from block import Block
from transaction import Transaction
from wallet import Wallet

import utility.constants as constants
from time import time
from copy import deepcopy
from flask import jsonify

# The reward we give to miners (for creating a new block)
MINING_REWARD = 10

print(__name__)


class Blockchain:
    """The Blockchain class manages the chain of blocks as well as open
    transactions and the node on which it's running.

    Attributes:
        :chain: The list of blocks
        :open_transactions (private): The list of open transactions
        :hosting_node: The connected node (which runs the blockchain).
    """

    def __init__(self, public_key, node_id):
        """The constructor of the Blockchain class."""
        # Our starting block for the blockchain
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing our (empty) blockchain list
        self.chain = [genesis_block]
        # Unhandled transactions
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    # This turns the chain attribute into a property with a getter (the method
    # below) and a setter (@chain.setter)
    @property
    def chain(self):
        return self.__chain[:]

    # The setter for the chain property
    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        """Returns a copy of the open transactions list."""
        return self.__open_transactions[:]

    def load_data(self):
        """Initialize blockchain + open transactions data from a file."""
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                #convert from json to list
                blockchain = json.loads(file_content[0][:-1])
                # We need to convert  the loaded data because Transactions
                # should use OrderedDict
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction.to_transaction_from_dict(tx) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'],
                        block['previous_hash'],
                        converted_tx,
                        block['proof'],
                        block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                # We need to convert  the loaded data because Transactions
                # should use OrderedDict
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction.to_transaction_from_dict(tx)
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            if len(self.chain) > 1:
                print('error accured while loading data!')
        finally:
            print('loading data completed!')

    def save_data(self):
        """Save blockchain + open transactions snapshot to a file."""
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                saveable_chain = [
                    block.__dict__ for block in
                    [
                        Block(block_el.index,
                              block_el.previous_hash,
                              [tx.__dict__ for tx in block_el.transactions],
                              block_el.proof,
                              block_el.timestamp) for block_el in self.__chain
                    ]
                ]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')

    def proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the
        previous block and a random number (which is guessed until it fits)."""
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        """Calculate and return the balance for a participant.
        """
        if sender is None:
            if self.public_key is None:
                return None
            participant = self.public_key
        else:
            participant = sender
        # Fetch a list of all sent coin amounts for the given person (empty
        # lists are returned if the person was NOT the sender)
        # This fetches sent amounts of transactions that were already included
        # in blocks of the blockchain
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.__chain]
        # Fetch a list of all sent coin amounts for the given person (empty
        # lists are returned if the person was NOT the sender)
        # This fetches sent amounts of open transactions (to avoid double
        # spending)
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions
            if tx.sender == participant
        ]
        tx_sender.append(open_tx_sender)
        amount_sent = self.get_sum_of_sums_list(input_list = tx_sender)
        # This fetches received coin amounts of transactions that were already
        # included in blocks of the blockchain
        # We ignore open transactions here because you shouldn't be able to
        # spend coins before the transaction was confirmed + included in a
        # block
        tx_recipient = [
            [
                tx.amount for tx in block.transactions
                if tx.recipient == participant
            ] for block in self.__chain
        ]
        amount_received = self.get_sum_of_sums_list(input_list = tx_recipient)
        # Return the total balance
        return amount_received - amount_sent


    def get_sum_of_sums_list(self, input_list, initial_value=0):
        '''returns the sum of all the sums in an input list of lists'''
        return reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                                if len(tx_amt) > 0 else tx_sum + 0, #if inner list is empty add 0 and continue
                                input_list, initial_value)

    def get_last_blockchain_value(self):
        """ Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]




    def add_transaction(self, recipient, sender, signature, amount, timeStamp):
        """ Append a new value as well as the last blockchain value to the blockchain."""
        
        transaction = Transaction(sender, recipient, signature, amount, timeStamp)
        if not Verification.verify_transaction(transaction, self.get_balance):
            return False
        if not Transaction.contains_transaction(self.__open_transactions, transaction):
            self.__open_transactions.append(transaction)
            self.save_data()
            return broadcast_transaction(self.__peer_nodes, deepcopy(transaction))
        return True



    def mine_block(self):
        """Create a new block and add open transactions to it."""
        # Fetch the currently last block of the blockchain
        if self.public_key is None:
            return None
        last_block = self.__chain[-1]
        # Hash the last block (=> to be able to compare it to the stored hash
        # value)
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()

        reward_transaction = Transaction(
            constants.MINING, self.public_key, '', constants.MINING_REWARD, time())
        # Copy transaction instead of manipulating the original
        # open_transactions list
        # This ensures that if for some reason the mining should fail,
        # we don't have the reward transaction stored in the open transactions
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        block, self.resolve_conflicts = broadcast_block(self.__peer_nodes, block)
        if self.resolve_conflicts:
            self.resolve()
        return block

    def add_block(self, block):
        """Add a block which was received via broadcasting."""
        #if already has it
        if Block.Contains_Block(self.chain, block):
            return True
        
        # Create a list of transaction objects
        transactions = [Transaction(
            tx['sender'],
            tx['recipient'],
            tx['signature'],
            tx['amount'],
            tx['time']) for tx in block['transactions']]
        # Validate the proof of work of the block and store the result (True
        # or False) in a variable
        proof_is_valid = Verification.valid_proof(transactions[:-1], #the last tx is the mining so it's ignored
                                                 block['previous_hash'], 
                                                 block['proof'])
        # Check if previous_hash stored in the block is equal to the local
        # blockchain's last block's hash and store the result in a block
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        # Create a Block object
        converted_block = Block(
            block['index'],
            block['previous_hash'],
            transactions,
            block['proof'],
            block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        # Check which open transactions were included in the received block
        # and remove them

        for itx in block['transactions']:
            for opentx in stored_transactions:
                if (opentx.sender == itx['sender'] and
                        opentx.recipient == itx['recipient'] and
                        opentx.amount == itx['amount'] and
                        opentx.signature == itx['signature'] and
                        opentx.time == itx['time']):
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        #broadcast the new block to other peer nodes

        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            farward_block = deepcopy(block)
            try:
                response = requests.post(url, json={'block': farward_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
                    self.resolve()
                    self.resolve_conflicts = False
            except requests.exceptions.ConnectionError:
                continue

        return True



    def replace_chain(self, input_chain, input_open_tx):
        if Blockchain.sameChains(input_chain, self.chain):
            return True

        if len(input_chain) > len(self.chain):
            self.chain = input_chain
            self.__open_transactions = input_open_tx
            self.save_data()

        broadcast_chain_all_nodes(self.__peer_nodes, self.__chain, self.__open_transactions, Blockchain)
        


    def resolve(self):
        """Checks all peer nodes' blockchains and replaces the local one with
        longer valid ones."""
        # Initialize the winner chain with the local chain
        # winner_chain,winner_open_transactions, replace  = broadcast_chain(self.__peer_nodes, self.__chain,self.__open_transactions)
        # self.resolve_conflicts = False
        # Replace the local chain with the winner chain
        # self.chain = winner_chain
        # if replace:
            # self.__open_transactions = []
            # self.__open_transactions = winner_open_transactions
        # self.replace_chain(self.chain, self.__open_transactions)
        return broadcast_chain_all_nodes(self.__peer_nodes,self.__chain,self.__open_transactions, Blockchain)
        # return replace


    def add_peer_node(self, node):
        """Adds a new node to the peer node set.

        Arguments:
            :node: The node URL which should be added.
        """
        self.__peer_nodes.add(node)
        self.resolve()
        self.save_data()

    def remove_peer_node(self, node):
        """Removes a node from the peer node set.

        Arguments:
            :node: The node URL which should be removed.
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """Return a list of all connected peer nodes."""
        return list(self.__peer_nodes)
    

    @staticmethod
    def prepare_chain_to_json(inputChain):
        dict_chain = [block.__dict__.copy() for block in inputChain]
        for dict_block in dict_chain:
            dict_block['transactions'] = [
                tx.__dict__ for tx in dict_block['transactions']]
        return dict_chain
    
    
    @staticmethod
    def prepare_transactions_List_to_json(inputTxList):
        return [tx.__dict__ for tx in inputTxList]

    @staticmethod
    def convert_chain_from_json(inputChain):
        list_chain = [Block.convert_from_json(block) for block in inputChain]
        return list_chain

    @staticmethod
    def convert_open_tx_from_json(inputTx):
        open_tx = [Transaction.to_transaction_from_dict(tx) for tx in inputTx]
        return open_tx
    
    
    @staticmethod
    def sameChains(chain1 , chain2):
        len1 = len(chain1)        
        len2 = len(chain2)
        if len1 is not len2:
            return False
        for i in range(len1):
            # print('sameChains')
            # print(chain1[i])
            # print(chain2[i])
            if not Block.sameBlock(chain1[i],chain2[i]):
                return False
        return True