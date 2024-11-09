import os
import random
import string
import time
import telebot
import web3
import secrets
from eth_account import Account
from flask import Flask, request

app = Flask(__name__)

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

# List to store user wallet information (Replace with secure storage in production)
user_wallets = []


def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    public_key = Account.from_key(private_key)
    user_wallets.append(private_key)
    return private_key, public_key


@app.route("/start", methods=["POST"])
def start():
    bot.send_message(request.json['chat_id'], """Welcome to the Ethereum wallet bot! \U0001F916

    I can help you create a wallet and send and receive ETH. Here are the commands you can use:

    /help - Show all the commands
    /createWallet - Create a new wallet                                            
    /importWallet - Import your existing wallet using the private key
    /balance - Show your ETH balance
    /send - Send ETH or any other token

    Enjoy! \U0001F680""")
    return "OK"


@app.route("/createWallet", methods=["POST"])
def create_wallet_handler():
    private_key, public_key = create_wallet()
    bot.send_message(request.json['chat_id'], f"Your wallet has been created! Here are your keys:\nPrivate key: {private_key}\nPublic key: {public_key.address}")
    return "OK"


@app.route("/importWallet", methods=["POST"])
def import_wallet_command():
    private_key = request.json['private_key']
    if is_valid_private_key(private_key):
        user_wallets.append(private_key)
        public_key = Account.from_key(private_key)
        bot.send_message(request.json['chat_id'], f"Congrats! Your wallet has been imported.\n\nHere is your public key: {public_key.address}")
    else:
        bot.send_message(request.json['chat_id'], "Invalid private key. Please enter a valid private key in hex format starting with '0x'.")
    return "OK"


def is_valid_private_key(private_key):
    try:
        test = Account.from_key(private_key)
        return True
    except Exception:
        return False


@app.route("/balance", methods=["POST"])
def balance_command():
    if len(user_wallets) > 0:
        w3 = web3.Web3(web3.Web3.HTTPProvider('https://goerli.infura.io/v3/INSERT YOUR API KEY HERE'))
        private_key = user_wallets[0]
        public_key = Account.from_key(private_key)
        balance_wei = w3.eth.get_balance(public_key.address)
        balance_eth = balance_wei / 1e18
        formatted_balance = "{:.4f}".format(balance_eth)
        bot.send_message(request.json['chat_id'], f"Your ETH balance: {formatted_balance} ETH")
    else:
        bot.send_message(request.json['chat_id'], "You need to create or import a wallet first. Use /createWallet or /importWallet to create or import a wallet.")
    return "OK"


@app.route("/send", methods=["POST"])
def send_command():
    amount = request.json['amount']
    receiver_address = request.json['receiver_address']
    private_key = user_wallets[0]
    try:
        tx_hash = send_transaction(private_key, receiver_address, amount)
        bot.send_message(request.json['chat_id'], f"Transaction sent successfully! Transaction Hash: {tx_hash.hex()}")
    except Exception as e:
        bot.send_message(request.json['chat_id'], f"Error occurred while sending transaction: {str(e)}")
    return "OK"


def send_transaction(private_key, receiver_address, amount):
    w3 = web3.Web3(web3.Web3.HTTPProvider('https://goerli.infura.io/v3/INSERT YOUR API KEY HERE'))
    account = Account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    gas_limit = 21000  # Default gas limit for a simple transfer
    value = w3.to_wei(amount, 'ether')
    transaction = {
        'nonce': nonce,
        'to': receiver_address,
        'value': value,
        'gasPrice': gas_price,
        'gas': gas_limit
    }
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    return tx_hash


if __name__ == "__main__":
    app.run(debug=True)
