from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

from utility.message_handler import single_line_response
from time import time
from utility import constants
from utility import broadcast
app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), constants.STATUS_201
    else:
        response = {
            'message': 'Saving the keys failed.'
        }
        return jsonify(response), constants.STATUS_500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), constants.STATUS_201
    else:
        response = {
            'message': 'Loading the keys failed.'
        }
        return jsonify(response), constants.STATUS_500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance is not None:
        response = {
            'message': 'Fetched balance successfully.',
            'funds': balance
        }
        return jsonify(response), constants.STATUS_200
    else:
        response = {
            'messsage': 'Loading balance failed.',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), constants.STATUS_500


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        response = single_line_response('No data found.')
        return jsonify(response), constants.STATUS_400
    required = ['sender', 'recipient', 'amount', 'signature', 'time']
    if not all(key in values for key in required):
        response = single_line_response('Some data is missing.')
        return jsonify(response), constants.STATUS_400
    success = blockchain.add_transaction(
        values['recipient'],
        values['sender'],
        values['signature'],
        values['amount'],
        values['time'])
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': values['sender'],
                'recipient': values['recipient'],
                'amount': values['amount'],
                'signature': values['signature'],
                'time': values['time']
            }
        }
        return jsonify(response), constants.STATUS_201
    else:
        response = single_line_response('Creating a transaction failed.')
        return jsonify(response), constants.STATUS_500


@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = single_line_response('No data found.')
        return jsonify(response), constants.STATUS_400
    if 'block' not in values:
        response = single_line_response('Some data is missing.')
        return jsonify(response), constants.STATUS_400
    block = values['block']
    if block['index'] == blockchain.chain[-1].index + 1: #if it's the next block for my chain
        if blockchain.add_block(block):
            response = single_line_response('Block added')
            return jsonify(response), constants.STATUS_201
        else:
            response = single_line_response('Block seems invalid.')
            return jsonify(response), constants.STATUS_409
    elif block['index'] > blockchain.chain[-1].index: # block is way a head
        response = single_line_response('Blockchain seems to differ from local blockchain.')
        blockchain.resolve_conflicts = True
        resolve_conflicts()
        blockchain.resolve_conflicts = False
        return jsonify(response), constants.STATUS_200
    else:
        response = {
            'message': 'Blockchain seems to be shorter, block not added'}
        return jsonify(response), constants.STATUS_409


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key is None:
        response = single_line_response('No wallet set up.')
        return jsonify(response), constants.STATUS_400

    values = request.get_json()
    if not values:
        response = single_line_response('No data found.')
        return jsonify(response), constants.STATUS_400

    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        response = single_line_response('Required data is missing.')
        return jsonify(response), constants.STATUS_400
        
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    timeStamp = time()
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount, timeStamp)
    if success:
        response = {
            'message': 'Successfully added transaction.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature,
                'time': timeStamp
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), constants.STATUS_201
    else:
        response = single_line_response('Creating a transaction failed.')
        return jsonify(response), constants.STATUS_500


@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.resolve_conflicts:
        # response = {'message': 'Resolve conflicts first, block not added!'}
        resolve_conflicts()
        # return jsonify(response), constants.STATUS_409
    block = blockchain.mine_block()
    if block is not None:
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [
            tx.__dict__ for tx in dict_block['transactions']]
        response = {
            'message': 'Block added successfully.',
            'block': dict_block,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), constants.STATUS_201
    else:
        response = {
            'message': 'Adding a block failed.',
            'wallet_set_up': wallet.public_key is not None
        }
        return jsonify(response), constants.STATUS_500


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced!'}
    else:
        response = {'message': 'Local chain kept!'}
    return jsonify(response), constants.STATUS_200


@app.route('/transactions', methods=['GET'])
def get_open_transaction():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), constants.STATUS_200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    # dict_chain = blockchain.prepare_chain_to_json(chain_snapshot)
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [
            tx.__dict__ for tx in dict_block['transactions']]
    return jsonify(dict_chain), constants.STATUS_200

@app.route('/chain', methods=['POST'])
def post_chain():
    
    values = request.get_json()
    chain_received = values['chain']
    open_tx_received = values['open_tx']

   
    blockchain.replace_chain(blockchain.convert_chain_from_json(chain_received), blockchain.convert_open_tx_from_json(open_tx_received))
    return 'somthing'
    # todo fix the transforamtion from json and object


@app.route('/node', methods=['POST'])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data attached.'
        }
        return jsonify(response), constants.STATUS_400
    if 'node' not in values:
        response = {
            'message': 'No node data found.'
        }
        return jsonify(response), constants.STATUS_400
    node = values['node']
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added successfully.',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), constants.STATUS_201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url is None:
        response = {
            'message': 'No node found.'
        }
        return jsonify(response), constants.STATUS_400
    blockchain.remove_peer_node(node_url)
    response = {
        'message': 'Node removed',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), constants.STATUS_200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), constants.STATUS_200


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)
