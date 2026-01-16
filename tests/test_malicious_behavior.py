from client.node import Node
from testing_utils import ONE_ETH, EthTools, RevertException
from client.utils import APPEAL_PERIOD, Contract, sign, ChannelStateMessage, Signature
import pytest
from hexbytes import HexBytes


def test_invalid_signature_on_close(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that contract rejects closure with invalid signature"""
    alice.send(chan.address, ONE_ETH)
    
    # Create state with wrong signature
    fake_sig = Signature((27, HexBytes(b'\x00'*32), HexBytes(b'\x00'*32)))
    
    with pytest.raises(RevertException):
        chan.transact(alice, "oneSidedClose", (9*ONE_ETH, ONE_ETH, 1, 27, b'\x00'*32, b'\x00'*32))


def test_wrong_serial_number_appeal(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that appeal with same or lower serial number is rejected"""
    alice.send(chan.address, ONE_ETH)
    alice.send(chan.address, ONE_ETH)
    
    # Alice closes with latest state
    alice.close_channel(chan.address)
    
    # Try to appeal with same serial number
    msg = bob.get_current_channel_state(chan.address)
    v, r, s = msg.sig
    
    with pytest.raises(RevertException):
        chan.transact(bob, "appealClosure", (msg.balance1, msg.balance2, msg.serial_number, v, r, s))


def test_forged_signature_by_third_party(eth_tools: EthTools, alice: Node, bob: Node, charlie: Node, chan: Contract) -> None:
    """Test that contract rejects signatures from non-participants"""
    alice.send(chan.address, ONE_ETH)
    
    # Charlie tries to forge a state
    fake_msg = ChannelStateMessage(chan.address, 5*ONE_ETH, 5*ONE_ETH, 10)
    signed_by_charlie = sign(charlie.private_key, fake_msg)
    v, r, s = signed_by_charlie.sig
    
    with pytest.raises(RevertException):
        chan.transact(alice, "oneSidedClose", (5*ONE_ETH, 5*ONE_ETH, 10, v, r, s))


def test_out_of_order_updates(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that nodes reject out-of-order state updates"""
    alice.send(chan.address, ONE_ETH)
    state1 = alice.get_current_channel_state(chan.address)
    
    alice.send(chan.address, ONE_ETH)
    alice.send(chan.address, ONE_ETH)
    
    # Try to send old state to Bob (should be ignored)
    initial_serial = bob.get_current_channel_state(chan.address).serial_number
    bob.receive_funds(state1)
    
    # Bob should still have the latest state, not the old one
    assert bob.get_current_channel_state(chan.address).serial_number == initial_serial


def test_invalid_balance_sum(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that contract rejects states where balances don't sum to total deposit"""
    alice.send(chan.address, ONE_ETH)
    msg = alice.get_current_channel_state(chan.address)
    v, r, s = msg.sig
    
    # Try to close with invalid balance sum
    with pytest.raises(RevertException):
        chan.transact(alice, "oneSidedClose", (5*ONE_ETH, 6*ONE_ETH, msg.serial_number, v, r, s))


def test_appeal_after_timeout(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that appeals are rejected after appeal period expires"""
    alice.send(chan.address, ONE_ETH)
    old_state = alice.get_current_channel_state(chan.address)
    
    alice.send(chan.address, ONE_ETH)
    
    # Alice closes with old state
    alice.close_channel(chan.address, old_state)
    
    # Wait for appeal period to expire
    eth_tools.mine_blocks(APPEAL_PERIOD + 1)
    
    # Bob tries to appeal after timeout
    msg = bob.get_current_channel_state(chan.address)
    v, r, s = msg.sig
    
    with pytest.raises(RevertException):
        chan.transact(bob, "appealClosure", (msg.balance1, msg.balance2, msg.serial_number, v, r, s))


def test_double_withdrawal_prevention(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that same party cannot withdraw twice"""
    alice.send(chan.address, ONE_ETH)
    alice.close_channel(chan.address)
    
    eth_tools.mine_blocks(APPEAL_PERIOD + 1)
    
    # Alice withdraws once
    alice.withdraw_funds(chan.address)
    
    # Try to withdraw again - should fail at node level
    with pytest.raises(Exception):
        alice.withdraw_funds(chan.address)


def test_negative_amount_send(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that sending negative or zero amounts is rejected"""
    with pytest.raises(Exception):
        alice.send(chan.address, 0)
    
    with pytest.raises(Exception):
        alice.send(chan.address, -1*ONE_ETH)


def test_insufficient_balance_send(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that sending more than available balance is rejected"""
    # Alice has 10 ETH in channel
    with pytest.raises(Exception):
        alice.send(chan.address, 11*ONE_ETH)


def test_close_with_higher_serial_than_actual(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    """Test that closing with fabricated higher serial number fails signature validation"""
    alice.send(chan.address, ONE_ETH)
    
    # Create fake state with higher serial but wrong signature
    fake_msg = ChannelStateMessage(chan.address, 9*ONE_ETH, ONE_ETH, 999)
    signed_fake = sign(alice.private_key, fake_msg)
    v, r, s = signed_fake.sig
    
    # This should fail because Bob never signed this state
    with pytest.raises(RevertException):
        chan.transact(alice, "oneSidedClose", (9*ONE_ETH, ONE_ETH, 999, v, r, s))
