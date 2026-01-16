# Project Structure

```
ex4--7-/
│
├── client/                          # Python Lightning Node Implementation
│   ├── __init__.py                  # Package initializer
│   ├── lightning_node.py            # Main LightningNode class (Milestone 3)
│   ├── network.py                   # Network simulation for message passing
│   ├── node.py                      # Abstract Node base class
│   └── utils.py                     # Utilities (signing, validation, Contract wrapper)
│
├── contracts/                       # Solidity Smart Contracts
│   ├── Channel.sol                  # Main payment channel contract (Milestone 2)
│   └── ChannelInterface.sol         # Contract interface definition
│
├── tests/                           # Test Suite (Milestone 4)
│   ├── conftest.py                  # Pytest fixtures (auto-start Hardhat)
│   ├── test_basic_scenarios.py      # 7 basic functionality tests
│   ├── test_malicious_behavior.py   # 10 security/attack tests
│   └── testing_utils.py             # Test helper utilities
│
├── scripts/                         # Deployment scripts directory
│   └── .gitkeep                     # Placeholder
│
├── .gitignore                       # Git ignore patterns
├── hardhat.config.js                # Hardhat configuration (Milestone 1)
├── package.json                     # Node.js dependencies
├── package-lock.json                # Locked Node.js dependencies
├── requirements.txt                 # Python dependencies (Milestone 1)
├── test_web3_connection.py          # Web3 connectivity test (Milestone 1)
│
├── README.md                        # Main documentation with milestone details
├── PROOF.md                         # Executive summary of implementation
├── VERIFICATION.md                  # Detailed line-by-line verification
└── VERIFICATION_STEPS.md            # Step-by-step commands to verify

Generated at runtime (gitignored):
├── node_modules/                    # Node.js packages (npm install)
├── venv/                            # Python virtual environment
├── cache/                           # Hardhat compilation cache
├── artifacts/                       # Compiled contract artifacts
└── __pycache__/                     # Python bytecode cache
```

## File Descriptions

### Core Implementation Files

**contracts/Channel.sol** (150 lines)
- Constructor with state storage
- oneSidedClose() for channel closure
- appealClosure() for fraud prevention
- withdrawFunds() for settlement
- _verifySig() for signature verification

**client/lightning_node.py** (230 lines)
- LightningNode class implementation
- send() for off-chain transfers
- close_channel() for blockchain submission
- appeal_closed_chan() for fraud detection
- receive_funds() and ack_transfer() for message handling

**client/utils.py** (150 lines)
- sign() and validate_signature() functions
- Contract wrapper class for blockchain interaction
- ChannelStateMessage dataclass
- Compilation utilities

### Test Files

**tests/test_basic_scenarios.py** (160 lines)
- 7 tests covering normal workflows
- Channel creation, transfers, closure, settlement

**tests/test_malicious_behavior.py** (140 lines)
- 10 tests covering attack scenarios
- Invalid signatures, wrong serials, fraud attempts

**tests/conftest.py** (170 lines)
- Pytest fixtures for test setup
- Auto-start Hardhat node
- Create test accounts and nodes

### Configuration Files

**hardhat.config.js** (10 lines)
- Solidity version: 0.8.19
- Network: localhost (127.0.0.1:8545)

**requirements.txt** (3 lines)
- web3
- pytest
- py-solc-x

**package.json** (15 lines)
- hardhat
- @nomicfoundation/hardhat-toolbox

## Total Lines of Code

- Solidity: ~150 lines
- Python: ~750 lines
- Tests: ~470 lines
- **Total**: ~1,370 lines

## Key Directories

- **Source Code**: `client/` + `contracts/` = Core implementation
- **Tests**: `tests/` = Verification suite
- **Docs**: `*.md` files = Documentation and proof
- **Config**: Root level config files = Environment setup
