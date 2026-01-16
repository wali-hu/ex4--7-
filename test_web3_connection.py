#!/usr/bin/env python3
"""Test script for web3.py connectivity to Hardhat"""

from web3 import Web3

def test_web3_connection():
    # Connect to Hardhat local node
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    
    # Test connection
    if w3.is_connected():
        print(" Web3 connected to Hardhat successfully!")
        
        # Get block number
        block_number = w3.eth.block_number
        print(f" Current block number: {block_number}")
        
        # Get accounts
        accounts = w3.eth.accounts
        print(f" Available accounts: {len(accounts)}")
        print(f" First account: {accounts[0]}")
        
        # Get balance
        balance = w3.eth.get_balance(accounts[0])
        balance_eth = w3.from_wei(balance, 'ether')
        print(f" Balance: {balance_eth} ETH")
        
        return True
    else:
        print(" Failed to connect to Hardhat")
        return False

if __name__ == "__main__":
    test_web3_connection()
