from flask import Flask, jsonify, request
from configparser import ConfigParser

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

import json
import sqlite3
from ethtoken.abi import EIP20_ABI

app = Flask(__name__)


# Secrets config
config = ConfigParser()
config.read('secrets.ini')

private_key = config.get('secrets', 'private_key')
contract_address = config.get('secrets', 'contract_address')
sender_address = config.get('secrets', 'sender_address')
web3_provider = config.get('secrets', 'web3_provider')

# Ethereum config
w3 = Web3(Web3.HTTPProvider(web3_provider))
# Required if you use testnet
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
acct = w3.eth.account.privateKeyToAccount(private_key)
unicorns = w3.eth.contract(address=contract_address, abi=EIP20_ABI)


def send_tokens(receiver_address):
    nonce = w3.eth.getTransactionCount(sender_address)
    unicorn_txn = unicorns.functions.transfer(
            receiver_address,
            1000000000000000000,
        ).buildTransaction({
            # Change chainId according to https://chainid.network/
            'chainId': 4,
            'gas': 150000,
            'gasPrice': w3.toWei('1', 'gwei'),
            'nonce': nonce,
        })
    signed_txn = w3.eth.account.signTransaction(unicorn_txn, private_key=private_key)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    return w3.toHex(w3.sha3(signed_txn.rawTransaction))

@app.route('/')
def home():
    return jsonify(node_status=w3.isConnected())

@app.route('/get_token')
def get_token():
    if 'address' in request.args:
        receiver_address = request.args.get("address")

        conn = sqlite3.connect('droplink.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM addresses WHERE address='%s'" % (receiver_address))
        previous_receivers = cursor.fetchone()
        if previous_receivers:
            return jsonify(message='This address already received membership token', status=0)
        else:
            tx_hash = send_tokens(receiver_address)
            conn = sqlite3.connect('droplink.db')
            cur = conn.cursor()
            sql = "INSERT INTO addresses(address) VALUES('%s')" % (receiver_address)
            cur.execute(sql)
            conn.commit()
            return jsonify(message='DAO Membership token (MOK) has been sent', tx_hash=tx_hash, status=1)

    else:
        return jsonify(message='Receiver address is missing', status=0)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
