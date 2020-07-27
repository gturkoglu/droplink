import needle_sdk
from flask import Flask, jsonify, request

from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

from configparser import ConfigParser

import json
import sqlite3
from ethtoken.abi import EIP20_ABI

app = Flask(__name__)
needle_sdk.start(flask_app=app)

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

@app.after_request
def apply_caching(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.route('/')
def home():
    return jsonify(node_status=w3.isConnected())

@app.route('/login', methods=["POST"])
def login():
    if 'username' and 'password' in request.json:
        username = request.json["username"]
        password = request.json["password"]
        try:
            conn = sqlite3.connect('droplink.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password))
            user_auth = cursor.fetchone()
            if user_auth:
                import uuid
                session = uuid.uuid4()
                conn = sqlite3.connect('droplink.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO sessions(username, session) VALUES('%s', '%s')" % (username, session))
                conn.commit()
                return jsonify(message='User authentiated', status=1, session=session)
            else:
                return 'Bad credentials'
        except:
            return 'Something wrong'
    else:
        return 'Missing'

@app.route('/register', methods=["POST"])
def register():
    import coinaddr
    if 'address' and 'username' and 'password' in request.json:
        address = request.json["address"]
        username = request.json["username"]
        password = request.json["password"]
        if coinaddr.validate('eth', address).valid:
            conn = sqlite3.connect('droplink.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username='%s'" % (username))
            registered_usernames = cursor.fetchone()
            if registered_usernames:
                return jsonify(message='Username unavailable', status=0)
            else:
                try:
                    conn = sqlite3.connect('droplink.db')
                    cur = conn.cursor()
                    sql = "INSERT INTO users(username, password, address, received) VALUES('%s', '%s', '%s', '%s')" % (username, password, address, 'False')
                    cur.execute(sql)
                    conn.commit()
                    return jsonify(message='Registration completed', status=1)
                except:
                    return jsonify(message='Failed for unknown reason', status=2)
                
        else: 
            return "FALSE"
    else:
        return abort(400)

@app.route('/change_address')
def change_address():
    if 'session' and 'address' in request.args:
        try:
            session = request.args.get("session")
            address = request.args.get("address")
            conn = sqlite3.connect("droplink.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM sessions WHERE session='%s'" % (session))
            username = cursor.fetchone()[0]
            try:
                import coinaddr
                if coinaddr.validate('eth', address).valid:
                    conn = sqlite3.connect("droplink.db")
                    cursor = conn.cursor()
                    sql = "UPDATE users SET address = '%s' WHERE username = '%s'" % (address, username)
                    cursor.execute(sql)
                    conn.commit()
                    return jsonify(message='Address is changed', status=1)
                else:
                    return jsonify(message='Bad Ethereum address', status=0)
            except:
                return jsonify(message='Database error, unknown reason', status=0)
        except:
            return jsonify(message='Database error, bad session token?', status=0)
    else:
        return jsonify(message='Args missing', status=0)

@app.route('/get_address')
def get_address():
    if 'session' in request.args:
        try:
            session = request.args.get("session")
            conn = sqlite3.connect("droplink.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM sessions WHERE session='%s'" % (session))
            username = cursor.fetchone()[0]
            try:
                conn = sqlite3.connect("droplink.db")
                cursor = conn.cursor()
                sql = "SELECT address FROM users WHERE username = '%s'" % (username)
                cursor.execute(sql)
                address = cursor.fetchone()[0]
                return jsonify(message=address, status=1)
            except:
                return jsonify(message='Database error, unknown reason', status=0)
        except:
            return jsonify(message='Database error, bad session token?', status=0)
    else:
        return jsonify(message='Args missing', status=0)

@app.route('/claim_token')
def claim_token():
    if 'session' in request.args:
        try:
            session = request.args.get("session")
            conn = sqlite3.connect("droplink.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM sessions WHERE session='%s'" % (session))
            username = cursor.fetchone()[0]
            try:
                conn = sqlite3.connect("droplink.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username='%s'" % (username))
                db_query = cursor.fetchone()
                is_received = db_query[3]
                receiver_address = db_query[2]
                if is_received == 'False':
                    try:
                        tx_hash = send_tokens(receiver_address)
                        conn = sqlite3.connect('droplink.db')
                        cur = conn.cursor()
                        sql = "UPDATE users SET received = 'True' WHERE username = '%s'" % (username)
                        cur.execute(sql)
                        conn.commit()
                        return jsonify(message='Membership token is sent', tx_hash=tx_hash, status=1)
                    except:
                        return jsonify(message='Transaction error', status=0)
                else:
                    return jsonify(message='User already received', status=0)
            except:
                return jsonify(message='Database error (2)', status=0)
        except:
            return jsonify(message='Database error (1)', status=0)
    else:
        return jsonify(message='Session token is misssing', status=0)

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
            try:
                tx_hash = send_tokens(receiver_address)
                conn = sqlite3.connect('droplink.db') 
                cur = conn.cursor()
                sql = "INSERT INTO addresses(address) VALUES('%s')" % (receiver_address)
                cur.execute(sql)
                conn.commit()
                return jsonify(message='DAO Membership token (MOK) has been sent', tx_hash=tx_hash, status=1)
            except:
                return jsonify(message='Bad Ethereum address', status=0)
    else:
        return jsonify(message='Receiver address is missing', status=0)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
