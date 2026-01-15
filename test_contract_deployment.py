#!/usr/bin/env python3
from web3 import Web3
import json

# Connect to Hardhat
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
assert w3.is_connected(), "Not connected to Hardhat"

# Load contract
with open('artifacts/contracts/Channel.sol/Channel.json') as f:
    contract_json = json.load(f)
    abi = contract_json['abi']
    bytecode = contract_json['bytecode']

# Get accounts
accounts = w3.eth.accounts
party1 = accounts[0]
party2 = accounts[1]

print(f"Party 1: {party1}")
print(f"Party 2: {party2}")

# Deploy contract
Channel = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Channel.constructor(party2, 60).transact({
    'from': party1,
    'value': w3.to_wei(10, 'ether')
})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress

print(f"\n✓ Contract deployed at: {contract_address}")

# Test contract state
channel = w3.eth.contract(address=contract_address, abi=abi)
print(f"✓ Party1: {channel.functions.party1().call()}")
print(f"✓ Party2: {channel.functions.party2().call()}")
print(f"✓ Total Deposit: {w3.from_wei(channel.functions.totalDeposit().call(), 'ether')} ETH")
print(f"✓ Appeal Period: {channel.functions.appealPeriodLen().call()} seconds")
print(f"✓ Channel Closed: {channel.functions.channelClosed().call()}")

print("\n✓ Milestone 2 (Part 1) Complete: Constructor & State Storage Working!")
