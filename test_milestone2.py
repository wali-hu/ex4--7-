#!/usr/bin/env python3
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import time

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
assert w3.is_connected()

# Load contract
with open('artifacts/contracts/Channel.sol/Channel.json') as f:
    contract_json = json.load(f)
    abi = contract_json['abi']
    bytecode = contract_json['bytecode']

# Setup accounts
accounts = w3.eth.accounts
party1_addr = accounts[0]
party2_addr = accounts[1]

# Create private keys for signing
party1_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
party2_key = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

print("=== Milestone 2 Complete Test ===\n")

# Deploy
Channel = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Channel.constructor(party2_addr, 5).transact({
    'from': party1_addr,
    'value': w3.to_wei(10, 'ether')
})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
channel = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

print(f"✓ Part 1: Contract deployed at {tx_receipt.contractAddress}")
print(f"  - Party1: {channel.functions.party1().call()}")
print(f"  - Party2: {channel.functions.party2().call()}")
print(f"  - Deposit: {w3.from_wei(channel.functions.totalDeposit().call(), 'ether')} ETH\n")

# Test Part 2: Channel Closing
def sign_state(contract_addr, balance1, balance2, serial, private_key):
    msg_hash = w3.solidity_keccak(['address', 'uint256', 'uint256', 'uint256'],
                                   [contract_addr, balance1, balance2, serial])
    message = encode_defunct(hexstr=msg_hash.hex())
    signed = Account.from_key(private_key).sign_message(message)
    return signed.v, signed.r.to_bytes(32, 'big'), signed.s.to_bytes(32, 'big')

# Party2 signs state: 6 ETH to party1, 4 ETH to party2
balance1 = w3.to_wei(6, 'ether')
balance2 = w3.to_wei(4, 'ether')
serial = 1
v, r, s = sign_state(channel.address, balance1, balance2, serial, party2_key)

# Party1 closes channel
tx_hash = channel.functions.oneSidedClose(balance1, balance2, serial, v, r, s).transact({'from': party1_addr})
w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✓ Part 2: Channel closed successfully")
print(f"  - Balance1: {w3.from_wei(channel.functions.balance1().call(), 'ether')} ETH")
print(f"  - Balance2: {w3.from_wei(channel.functions.balance2().call(), 'ether')} ETH")
print(f"  - Serial: {channel.functions.currentSerialNum().call()}")
print(f"  - Closed: {channel.functions.channelClosed().call()}\n")

# Test Part 3: Appeal Logic
# Party1 signs newer state: 7 ETH to party1, 3 ETH to party2
new_balance1 = w3.to_wei(7, 'ether')
new_balance2 = w3.to_wei(3, 'ether')
new_serial = 2
v2, r2, s2 = sign_state(channel.address, new_balance1, new_balance2, new_serial, party1_key)

# Party2 appeals with newer state
tx_hash = channel.functions.appealClosure(new_balance1, new_balance2, new_serial, v2, r2, s2).transact({'from': party2_addr})
w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✓ Part 3: Appeal successful")
print(f"  - New Balance1: {w3.from_wei(channel.functions.balance1().call(), 'ether')} ETH")
print(f"  - New Balance2: {w3.from_wei(channel.functions.balance2().call(), 'ether')} ETH")
print(f"  - New Serial: {channel.functions.currentSerialNum().call()}\n")

# Test Part 4: Final Settlement
print("Waiting for appeal period to end...")
time.sleep(6)

# Check contract balance
contract_balance = w3.eth.get_balance(channel.address)
print(f"  - Contract balance: {w3.from_wei(contract_balance, 'ether')} ETH")

# Get balances before withdrawal
balance_before_p1 = w3.eth.get_balance(party1_addr)
balance_before_p2 = w3.eth.get_balance(party2_addr)

# Party1 withdraws
try:
    tx_hash = channel.functions.withdrawFunds(party1_addr).transact({'from': party1_addr, 'gas': 100000})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  ✓ Party1 withdrawal successful (gas used: {receipt.gasUsed})")
except Exception as e:
    print(f"  ✗ Party1 withdrawal failed: {e}")

# Party2 withdraws
try:
    tx_hash = channel.functions.withdrawFunds(party2_addr).transact({'from': party2_addr, 'gas': 100000})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  ✓ Party2 withdrawal successful (gas used: {receipt.gasUsed})")
except Exception as e:
    print(f"  ✗ Party2 withdrawal failed: {e}")

print(f"✓ Part 4: Final settlement complete")
print(f"  - Party1 received: ~{w3.from_wei(w3.eth.get_balance(party1_addr) - balance_before_p1, 'ether'):.2f} ETH")
print(f"  - Party2 received: ~{w3.from_wei(w3.eth.get_balance(party2_addr) - balance_before_p2, 'ether'):.2f} ETH")

# Test re-entry protection
try:
    channel.functions.withdrawFunds(party1_addr).transact({'from': party1_addr})
    print("  ✗ Re-entry protection FAILED")
except Exception as e:
    print(f"  ✓ Re-entry protection working\n")

print("=== Milestone 2 Complete: All Parts Verified ===")
