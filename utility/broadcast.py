import requests
from block import Block
from transaction import Transaction
from utility.verification import Verification
from wallet import Wallet

def broadcast_transaction(peer_nodes, transaction):
    for node in peer_nodes:
        url = 'http://{}/broadcast-transaction'.format(node)
        try:
            response = requests.post(url,
                                        json={
                                            'sender': transaction.sender,
                                            'recipient': transaction.recipient,
                                            'amount': transaction.amount,
                                            'signature': transaction.signature,
                                            'time': transaction.time
                                        })
            if (response.status_code == 400 or response.status_code == 500):
                print('Transaction declined, needs resolving')
                return False
        except requests.exceptions.ConnectionError:
            print('broadcast_transaction: connection error')
            continue
    return True
        


def broadcast_block(peer_nodes, block):
    resolve_conflicts = False
    for node in peer_nodes:
        url = 'http://{}/broadcast-block'.format(node)
        converted_block = block.__dict__.copy()
        converted_block['transactions'] = [
            tx.__dict__ for tx in converted_block['transactions']]
        try:
            response = requests.post(url, json={'block': converted_block})
            if response.status_code == 400 or response.status_code == 500:
                print('Block declined, needs resolving')
            if response.status_code == 409:
                resolve_conflicts = True
        except requests.exceptions.ConnectionError:
            print('broadcast_block: connection error')
            continue
    return block , resolve_conflicts





# for when 2 nodes connect so they will know each others previous transactions
def broadcast_open_transactions(peer_nodes, open_transactions):
    transactionSet = set(open_transactions)
    for node in peer_nodes:
        url = 'http://{}/transactions'.format(node)
        try:
            # Send a request and store the response
            response = requests.get(url)
            # Retrieve the JSON data as a dictionary
            nodeTransactionList = response.json()
            # Convert the json 
            node_tx = [Transaction.to_transaction_from_dict(tx) for tx in nodeTransactionList]
            transactionSet = transactionSet.union(set(node_tx))

        except requests.exceptions.ConnectionError:
            continue
    return list(transactionSet)
    



def broadcast_chain(peer_nodes, selfChain,open_transactions, replace = False):
    # Initialize the winner chain with the local chain
    winner_chain = selfChain
    winner_open_transactions = open_transactions
    for node in peer_nodes:
        url = 'http://{}/chain'.format(node)
        try:
            # Send a request and store the response
            response = requests.get(url)
            # Retrieve the JSON data as a dictionary
            node_chain = response.json()
            # Convert the dictionary list to a list of block AND
            # transaction objects
            node_chain = [Block(block['index'], block['previous_hash'],
                    [Transaction.to_transaction_from_dict(tx)
                    for tx in block['transactions']],
                    block['proof'],
                    block['timestamp']) for block in node_chain
            ]
            node_chain_length = len(node_chain)
            local_chain_length = len(winner_chain)
            # Store the received chain as the current winner chain if it's
            # longer AND valid
            if (node_chain_length > local_chain_length and
                    Verification.verify_chain(node_chain)):
                winner_chain = node_chain
                url = 'http://{}/transactions'.format(node)
                try:
                    response = requests.get(url)
                    open_tx = response.json()
                    open_tx = [Transaction.to_transaction_from_dict(tx) for tx in open_tx]
                    winner_open_transactions = open_tx
                except requests.exceptions.ConnectionError:
                    continue
                replace = True
        except requests.exceptions.ConnectionError:
            continue
    return winner_chain, winner_open_transactions, replace






def broadcast_chain_all_nodes(peer_nodes, selfChain,open_transactions, Blockchain):
    # Initialize the winner chain with the local chain
    for node in peer_nodes:
        url = 'http://{}/chain'.format(node)
        try:
            converted_chain = Blockchain.prepare_chain_to_json(selfChain)
            converted_open_transactions = Blockchain.prepare_transactions_List_to_json(open_transactions)
            response = requests.post(url, json={'chain': converted_chain, 
                                                'open_tx': converted_open_transactions })
        except requests.exceptions.ConnectionError:
            continue 
    return True



















