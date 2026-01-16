from typing import Dict, Optional, List, Any
from client.utils import ChannelStateMessage, EthereumAddress, IPAddress, PrivateKey, Signature, Contract, sign, validate_signature, APPEAL_PERIOD
from hexbytes import HexBytes
from eth_typing import HexAddress, HexStr
from client.network import Network, Message
from client.node import Node
from web3 import Web3


class LightningNode(Node):
    """represents a payment channel node that can support several payment channels."""

    def __init__(self, private_key: PrivateKey, eth_address: EthereumAddress, networking_interface: Network, ip: IPAddress, w3: Web3, contract_bytecode: str, contract_abi: Dict[str, Any]) -> None:
        self._private_key = private_key
        self._eth_address = eth_address
        self._network = networking_interface
        self._ip = ip
        self._w3 = w3
        self._bytecode = contract_bytecode
        self._abi = contract_abi
        self._channels: Dict[EthereumAddress, Dict[str, Any]] = {}

    def get_list_of_channels(self) -> List[EthereumAddress]:
        return list(self._channels.keys())

    def establish_channel(self, other_party_eth_address: EthereumAddress, other_party_ip_address: IPAddress,  amount_in_wei: int) -> EthereumAddress:
        if amount_in_wei <= 0:
            raise ValueError("Amount must be positive")
        if self._w3.eth.get_balance(self._eth_address) < amount_in_wei:
            raise ValueError("Insufficient funds")
        
        contract = Contract.deploy(self._w3, self._bytecode, self._abi, self, 
                                   (other_party_eth_address, APPEAL_PERIOD), 
                                   {'value': amount_in_wei})
        
        self._channels[contract.address] = {
            'other_party': other_party_eth_address,
            'other_ip': other_party_ip_address,
            'total_deposit': amount_in_wei,
            'balance1': amount_in_wei,
            'balance2': 0,
            'serial': 0,
            'last_state': None,
            'closed': False,
            'is_party1': True
        }
        
        self._network.send_message(other_party_ip_address, Message.NOTIFY_OF_CHANNEL, contract.address, self._ip)
        return contract.address

    @property
    def eth_address(self) -> EthereumAddress:
        return self._eth_address

    @property
    def ip_address(self) -> IPAddress:
        return self._ip

    @property
    def private_key(self) -> PrivateKey:
        return self._private_key

    def send(self, channel_address: EthereumAddress, amount_in_wei: int) -> None:
        if channel_address not in self._channels:
            raise Exception("Unknown channel")
        if amount_in_wei <= 0:
            raise Exception("Amount must be positive")
        
        chan = self._channels[channel_address]
        if chan['closed']:
            raise Exception("Channel is closed")
        
        my_balance = chan['balance1'] if chan['is_party1'] else chan['balance2']
        if my_balance < amount_in_wei:
            raise Exception("Insufficient balance")
        
        new_serial = chan['serial'] + 1
        if chan['is_party1']:
            new_b1 = chan['balance1'] - amount_in_wei
            new_b2 = chan['balance2'] + amount_in_wei
        else:
            new_b1 = chan['balance1'] + amount_in_wei
            new_b2 = chan['balance2'] - amount_in_wei
        
        msg = ChannelStateMessage(channel_address, new_b1, new_b2, new_serial)
        signed_msg = sign(self._private_key, msg)
        
        chan['balance1'] = new_b1
        chan['balance2'] = new_b2
        chan['serial'] = new_serial
        
        self._network.send_message(chan['other_ip'], Message.RECEIVE_FUNDS, signed_msg)

    def get_current_channel_state(self, channel_address: EthereumAddress) -> ChannelStateMessage:
        if channel_address not in self._channels:
            raise Exception("Unknown channel")
        
        state = self._channels[channel_address]['last_state']
        if state is None:
            chan = self._channels[channel_address]
            return ChannelStateMessage(channel_address, chan['balance1'], chan['balance2'], 0, Signature((0, b'\x00'*32, b'\x00'*32)))
        return state

    def close_channel(self, channel_address: EthereumAddress, channel_state: Optional[ChannelStateMessage] = None) -> bool:
        if channel_address not in self._channels:
            raise Exception("Unknown channel")
        
        chan = self._channels[channel_address]
        if chan['closed']:
            raise Exception("Channel already closed")
        
        contract = Contract(channel_address, self._abi, self._w3)
        
        if channel_state is None:
            channel_state = self.get_current_channel_state(channel_address)
        
        if channel_state.serial_number == 0:
            receipt = contract.transact(self, "oneSidedClose", (chan['balance1'], 0, 0, 0, b'\x00'*32, b'\x00'*32))
        else:
            v, r, s = channel_state.sig
            receipt = contract.transact(self, "oneSidedClose", 
                                      (channel_state.balance1, channel_state.balance2, 
                                       channel_state.serial_number, v, r, s))
        
        chan['closed'] = True
        return receipt['status'] == 1

    def appeal_closed_chan(self, contract_address: EthereumAddress) -> bool:
        if contract_address not in self._channels:
            return False
        
        chan = self._channels[contract_address]
        contract = Contract(contract_address, self._abi, self._w3)
        
        try:
            is_closed = contract.call("channelClosed")
            if not is_closed:
                return False
        except:
            return False
        
        if not chan['closed']:
            chan['closed'] = True
        
        on_chain_serial = contract.call("currentSerialNum")
        
        my_state = chan['last_state']
        if my_state is None or my_state.serial_number <= on_chain_serial:
            return False
        
        v, r, s = my_state.sig
        receipt = contract.transact(self, "appealClosure", 
                                   (my_state.balance1, my_state.balance2, 
                                    my_state.serial_number, v, r, s))
        return receipt['status'] == 1

    def withdraw_funds(self, contract_address: EthereumAddress) -> int:
        if contract_address not in self._channels:
            raise Exception("Unknown channel")
        
        contract = Contract(contract_address, self._abi, self._w3)
        
        try:
            balance = contract.call("getBalance", call_kwargs={'from': self._eth_address})
        except:
            raise Exception("Cannot withdraw yet")
        
        if balance > 0:
            contract.transact(self, "withdrawFunds", (self._eth_address,))
        
        del self._channels[contract_address]
        return balance

    def notify_of_channel(self, contract_address: EthereumAddress, other_party_ip_address: IPAddress) -> None:
        if contract_address in self._channels:
            return
        
        contract = Contract(contract_address, self._abi, self._w3)
        
        try:
            party1 = contract.call("party1")
            party2 = contract.call("party2")
            closed = contract.call("channelClosed")
            appeal_period = contract.call("appealPeriodLen")
            total = contract.call("totalDeposit")
        except:
            return
        
        if self._eth_address not in [party1, party2]:
            return
        if closed or appeal_period < APPEAL_PERIOD:
            return
        
        is_party1 = (self._eth_address == party1)
        
        self._channels[contract_address] = {
            'other_party': party2 if is_party1 else party1,
            'other_ip': other_party_ip_address,
            'total_deposit': total,
            'balance1': total,
            'balance2': 0,
            'serial': 0,
            'last_state': None,
            'closed': False,
            'is_party1': is_party1
        }

    def ack_transfer(self, msg: ChannelStateMessage) -> None:
        if msg.contract_address not in self._channels:
            return
        
        chan = self._channels[msg.contract_address]
        if not validate_signature(msg, chan['other_party']):
            return
        if msg.serial_number < chan['serial']:
            return
        
        my_old_balance = chan['balance1'] if chan['is_party1'] else chan['balance2']
        my_new_balance = msg.balance1 if chan['is_party1'] else msg.balance2
        
        if my_new_balance < my_old_balance:
            return
        
        chan['last_state'] = msg

    def receive_funds(self, state_msg: ChannelStateMessage) -> None:
        if state_msg.contract_address not in self._channels:
            return
        
        chan = self._channels[state_msg.contract_address]
        if not validate_signature(state_msg, chan['other_party']):
            return
        if state_msg.serial_number <= chan['serial']:
            return
        
        my_old_balance = chan['balance1'] if chan['is_party1'] else chan['balance2']
        my_new_balance = state_msg.balance1 if chan['is_party1'] else state_msg.balance2
        
        if my_new_balance < my_old_balance:
            return
        
        chan['balance1'] = state_msg.balance1
        chan['balance2'] = state_msg.balance2
        chan['serial'] = state_msg.serial_number
        chan['last_state'] = state_msg
        
        ack_msg = sign(self._private_key, ChannelStateMessage(
            state_msg.contract_address, state_msg.balance1, state_msg.balance2, state_msg.serial_number))
        
        self._network.send_message(chan['other_ip'], Message.ACK_TRANSFER, ack_msg)
