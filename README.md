# Lightning Network Payment Channel Implementation

**Student Name**: [Your Name]  
**Student ID**: [Your ID]

---

## Project Overview

This project implements a bidirectional payment channel system inspired by the Lightning Network. It enables two parties to conduct multiple off-chain transactions with on-chain settlement, featuring cryptographic security and fraud prevention mechanisms.

### Core Components

- **Smart Contract (Solidity)**: Manages fund locking, channel state, and secure settlement
- **Python Nodes**: Handle off-chain state updates and communication
- **Appeal Mechanism**: Prevents fraud through challenge periods
- **Comprehensive Tests**: Validates functionality and security

---

## Setup Instructions

### Prerequisites
- Node.js and npm (for Hardhat)
- Python 3.12+
- Git

### Installation Steps

1. **Navigate to project directory**:
   ```bash
   cd ex4--7-
   ```

2. **Install Hardhat dependencies**:
   ```bash
   npm install
   ```

3. **Create Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

1. **Run all tests** (Hardhat auto-starts):
   ```bash
   source venv/bin/activate
   python -m pytest tests/ -v
   ```

2. **Run specific test suites**:
   ```bash
   # Basic scenarios only
   python -m pytest tests/test_basic_scenarios.py -v
   
   # Malicious behavior tests only
   python -m pytest tests/test_malicious_behavior.py -v
   ```

---

## Implementation Details

### Milestone 1: Infrastructure Setup

**Objective**: Establish development environment with Hardhat blockchain and Python integration.

#### Part 1: Hardhat Project
- Initialized Hardhat with Solidity 0.8.19
- Configured localhost network (http://127.0.0.1:8545)
- Created scripts directory for deployment
- Tests auto-start Hardhat node via pytest fixture

**Files**: `hardhat.config.js`, `tests/conftest.py`

#### Part 2: Python Environment
- Created virtual environment with web3.py
- Installed dependencies: web3, pytest, py-solc-x
- Implemented connectivity test reading block numbers
- All imports working without errors

**Files**: `requirements.txt`, `test_web3_connection.py`

**Verification**: Environment setup complete, all dependencies functional.

---

### Milestone 2: Smart Contract Implementation

**Objective**: Implement Channel.sol with state management, closure, appeals, and settlement.

#### Part 1: Constructor & State Storage
```solidity
constructor(address payable _otherOwner, uint _appealPeriodLen) payable {
    party1 = payable(msg.sender);
    party2 = _otherOwner;
    totalDeposit = msg.value;
    appealPeriodLen = _appealPeriodLen;
}
```
- Stores participant addresses (party1, party2)
- Records deposit amount from msg.value
- Sets appeal period length
- Initializes channel as open

**Verification**: Contract deploys successfully, all state variables readable.

#### Part 2: Channel Closing Logic
```solidity
function oneSidedClose(uint _balance1, uint _balance2, uint serialNum,
                       uint8 v, bytes32 r, bytes32 s) external
```
- Validates caller is a participant
- Verifies signature using _verifySig()
- Records submitted state (balances, serial number)
- Sets closureTime to trigger appeal window
- Emits ChannelClosed event

**Verification**: Unilateral closure works, appeal timer starts correctly.

#### Part 3: Appeal/Challenge Logic
```solidity
function appealClosure(uint _balance1, uint _balance2, uint serialNum,
                       uint8 v, bytes32 r, bytes32 s) external
```
- Requires channel is closed and within appeal period
- Validates serial number is higher than current
- Verifies signature from other party
- Updates state if valid
- Emits AppealMade event

**Verification**: Newer states override older ones, fraud prevention working.

#### Part 4: Final Settlement
```solidity
function withdrawFunds(address payable destAddress) external
```
- Requires appeal period has expired
- Prevents double withdrawal with mapping
- Transfers correct balance to each party
- Re-entry protection via state update before transfer

**Verification**: Funds distributed correctly, double withdrawal blocked.

**Contract Location**: `contracts/Channel.sol`

---

### Milestone 3: Python Node Implementation

**Objective**: Create LightningNode class for off-chain state management and blockchain interaction.

#### Part 1: Node Class Structure
```python
class LightningNode(Node):
    def __init__(self, private_key, eth_address, ...):
        self._private_key = private_key
        self._eth_address = eth_address
        self._channels = {}
```
- Stores private key for signing
- Maintains Ethereum address
- Tracks multiple channels in dictionary
- Uses sign() utility for message signing

**Verification**: Nodes initialize correctly, can sign messages.

#### Part 2: State Update Messaging
```python
def send(self, channel_address, amount_in_wei):
    new_serial = chan['serial'] + 1
    msg = ChannelStateMessage(channel_address, new_b1, new_b2, new_serial)
    signed_msg = sign(self._private_key, msg)
    self._network.send_message(chan['other_ip'], Message.RECEIVE_FUNDS, signed_msg)
```
- Creates state updates with incremented serial numbers
- Signs updates with private key
- Sends via Network class (no blockchain transaction)
- Maintains local state synchronization

**Verification**: Off-chain transfers work, no blockchain transactions generated.

#### Part 2: Channel Closing Initiation
```python
def close_channel(self, channel_address, channel_state=None):
    contract = Contract(channel_address, self._abi, self._w3)
    receipt = contract.transact(self, "oneSidedClose", ...)
    chan['closed'] = True
```
- Submits last signed state to blockchain
- Includes signature for verification
- Marks channel as closed locally
- Prevents new updates after closure

**Verification**: On-chain closure triggered, state submitted with signature.

#### Part 3: Appeal Handler
```python
def appeal_closed_chan(self, contract_address):
    on_chain_serial = contract.call("currentSerialNum")
    if my_state.serial_number > on_chain_serial:
        receipt = contract.transact(self, "appealClosure", ...)
```
- Detects channel closure from blockchain
- Compares on-chain serial with local state
- Submits newer state if available
- Prevents fund theft through old states

**Verification**: Appeals work correctly, malicious closures defeated.

**Node Location**: `client/lightning_node.py`

---

### Milestone 4: Comprehensive Testing

**Objective**: Validate all functionality and security through automated tests.

#### Part 1: Basic Scenario Tests (7 tests)

1. **test_open_and_immediate_close** - Creates channel, closes immediately, verifies fund return
2. **test_nice_open_transfer_and_close** - 3 off-chain transfers, 0 blockchain transactions, correct settlement
3. **test_alice_tries_to_cheat** - Alice closes with old state, Bob appeals successfully
4. **test_channel_list_encapsulation** - Data structure isolation verified
5. **test_node_rejects_receive_message_of_unknown_channel** - Unknown channel handling
6. **test_close_by_alice_twice** - Contract-level double close prevention
7. **test_cant_close_channel_twice** - Node-level double close prevention

**Verification**: All basic workflows functional, 7/7 tests passing.

#### Part 2: Malicious Behavior Tests (10 tests)

1. **test_invalid_signature_on_close** - Fake signatures rejected
2. **test_wrong_serial_number_appeal** - Same/lower serial rejected
3. **test_forged_signature_by_third_party** - Non-participant signatures rejected
4. **test_out_of_order_updates** - Old states ignored
5. **test_invalid_balance_sum** - Balance validation enforced
6. **test_appeal_after_timeout** - Late appeals rejected
7. **test_double_withdrawal_prevention** - Double withdrawal blocked
8. **test_negative_amount_send** - Negative/zero amounts rejected
9. **test_insufficient_balance_send** - Over-balance transfers rejected
10. **test_close_with_higher_serial_than_actual** - Fabricated states rejected

**Verification**: All attacks blocked, no funds stealable, 10/10 tests passing.

**Test Locations**: `tests/test_basic_scenarios.py`, `tests/test_malicious_behavior.py`

---

## Test Results

```
========================= 17 passed, 1 warning =========================
```

All 17 tests passing:
- 7 basic scenario tests
- 10 malicious behavior tests

---

## Project Structure

```
ex4--7-/
├── contracts/
│   ├── Channel.sol              # Main payment channel contract
│   └── ChannelInterface.sol     # Contract interface
├── client/
│   ├── lightning_node.py        # Node implementation
│   ├── node.py                  # Abstract node class
│   ├── network.py               # Network simulation
│   └── utils.py                 # Utilities (signing, validation)
├── tests/
│   ├── conftest.py              # Test fixtures
│   ├── test_basic_scenarios.py  # Basic functionality tests
│   ├── test_malicious_behavior.py # Security tests
│   └── testing_utils.py         # Test utilities
├── hardhat.config.js            # Hardhat configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Key Features

### Security
- Cryptographic signature verification
- Serial number ordering enforcement
- Appeal period for fraud prevention
- Re-entry protection on withdrawals
- Balance validation on all operations

### Efficiency
- Multiple transactions without blockchain interaction
- State updates signed and exchanged directly
- Only channel open/close touch blockchain
- Significant gas savings

### Fraud Prevention
- Newer states always override older ones
- Appeal mechanism allows challenge period
- Both parties can close unilaterally
- No party can steal funds with old states

---

## How It Works

1. **Channel Creation**: Alice deploys contract with deposit, Bob is notified
2. **Off-Chain Transfers**: Parties exchange signed state updates directly
3. **Channel Closure**: Either party submits latest state to blockchain
4. **Appeal Period**: Other party can challenge with newer state
5. **Settlement**: After appeal period, funds distributed per final state

---

## Verification

All requirements from Milestones 1-4 have been implemented and verified.

See `VERIFICATION.md` and `PROOF.md` for detailed proof of implementation.
