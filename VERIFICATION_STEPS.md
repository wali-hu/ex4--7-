# Step-by-Step Verification Guide

This guide provides commands to verify the Lightning Network Payment Channel implementation from scratch.

---

## Prerequisites Check

Verify you have the required software installed:

```bash
# Check Node.js (should be v16 or higher)
node --version

# Check npm
npm --version

# Check Python (should be 3.12 or higher)
python3 --version

# Check Git
git --version
```

---

## Step 1: Clone and Navigate

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/wali-hu/ex4--7-.git

# Navigate to project directory
cd ex4--7-

# Check project structure
ls -la
```

**Expected output**: You should see directories: `client/`, `contracts/`, `tests/`, `scripts/`, and files like `README.md`, `hardhat.config.js`, `requirements.txt`

---

## Step 2: Install Hardhat Dependencies

```bash
# Install Node.js dependencies
npm install

# Verify Hardhat installation
npx hardhat --version
```

**Expected output**: Hardhat version should be displayed (e.g., 2.x.x)

---

## Step 3: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify activation (prompt should show (venv))
which python

# Install Python dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep -E "web3|pytest|py-solc-x"
```

**Expected output**: Should show web3, pytest, and py-solc-x packages installed

---

## Step 4: Test Web3 Connectivity (Optional)

This test requires Hardhat to be running in another terminal.

**Terminal 1:**
```bash
# Start Hardhat node
npx hardhat node
```

**Terminal 2:**
```bash
# Activate venv
source venv/bin/activate

# Test connectivity
python test_web3_connection.py
```

**Expected output**: "Connected! Current block: X"

**Note**: Stop Hardhat node (Ctrl+C) after this test. The main tests will auto-start it.

---

## Step 5: Run All Tests

```bash
# Make sure venv is activated
source venv/bin/activate

# Run all tests (Hardhat auto-starts)
python -m pytest tests/ -v

# Alternative: Run with more details
python -m pytest tests/ -v --tb=short
```

**Expected output**:
```
========================= 17 passed, 1 warning =========================

tests/test_basic_scenarios.py::test_open_and_immediate_close PASSED
tests/test_basic_scenarios.py::test_nice_open_transfer_and_close PASSED
tests/test_basic_scenarios.py::test_alice_tries_to_cheat PASSED
tests/test_basic_scenarios.py::test_channel_list_encapsulation PASSED
tests/test_basic_scenarios.py::test_node_rejects_receive_message_of_unknown_channel PASSED
tests/test_basic_scenarios.py::test_close_by_alice_twice PASSED
tests/test_basic_scenarios.py::test_cant_close_channel_twice PASSED
tests/test_malicious_behavior.py::test_invalid_signature_on_close PASSED
tests/test_malicious_behavior.py::test_wrong_serial_number_appeal PASSED
tests/test_malicious_behavior.py::test_forged_signature_by_third_party PASSED
tests/test_malicious_behavior.py::test_out_of_order_updates PASSED
tests/test_malicious_behavior.py::test_invalid_balance_sum PASSED
tests/test_malicious_behavior.py::test_appeal_after_timeout PASSED
tests/test_malicious_behavior.py::test_double_withdrawal_prevention PASSED
tests/test_malicious_behavior.py::test_negative_amount_send PASSED
tests/test_malicious_behavior.py::test_insufficient_balance_send PASSED
tests/test_malicious_behavior.py::test_close_with_higher_serial_than_actual PASSED
```

---

## Step 6: Run Specific Test Suites

### Basic Scenarios Only (7 tests)
```bash
python -m pytest tests/test_basic_scenarios.py -v
```

**Expected output**: 7 passed

### Malicious Behavior Only (10 tests)
```bash
python -m pytest tests/test_malicious_behavior.py -v
```

**Expected output**: 10 passed

---

## Step 7: Verify Contract Compilation

```bash
# Compile contracts
npx hardhat compile

# Check artifacts were created
ls -la artifacts/contracts/Channel.sol/
```

**Expected output**: Should see `Channel.json` and `Channel.dbg.json`

---

## Step 8: Verify Code Structure

### Check Smart Contract
```bash
# View contract structure
cat contracts/Channel.sol | grep -E "function|constructor|event"
```

**Expected output**: Should show functions like `oneSidedClose`, `appealClosure`, `withdrawFunds`

### Check Python Node
```bash
# View node methods
cat client/lightning_node.py | grep "def "
```

**Expected output**: Should show methods like `send`, `close_channel`, `appeal_closed_chan`

---

## Step 9: Verify Test Coverage

```bash
# Count test functions
grep -r "def test_" tests/*.py | wc -l
```

**Expected output**: 17 (7 basic + 10 malicious)

---

## Step 10: Review Documentation

```bash
# View README
cat README.md | head -50

# View verification proof
cat PROOF.md | head -30

# View detailed verification
cat VERIFICATION.md | head -50
```

---

## Troubleshooting

### If tests fail with "Hardhat node not running":
- Tests auto-start Hardhat, but if it fails, manually start in another terminal:
  ```bash
  npx hardhat node
  ```

### If Python imports fail:
- Ensure venv is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### If Hardhat compile fails:
- Clean and reinstall: 
  ```bash
  rm -rf artifacts cache
  npx hardhat clean
  npx hardhat compile
  ```

---

## Quick Verification Checklist

- [ ] Node.js and npm installed
- [ ] Python 3.12+ installed
- [ ] Dependencies installed (`npm install` and `pip install -r requirements.txt`)
- [ ] Virtual environment activated
- [ ] All 17 tests passing
- [ ] Contract compiles without errors
- [ ] Documentation files present (README.md, PROOF.md, VERIFICATION.md)

---

## Expected Final State

After following all steps, you should have:

1. **Working Environment**: Hardhat and Python properly configured
2. **Passing Tests**: 17/17 tests passing (7 basic + 10 malicious)
3. **Compiled Contract**: Channel.sol compiled successfully
4. **Functional Node**: LightningNode class working correctly
5. **Complete Documentation**: All milestone requirements verified

---

## Time Estimate

- Setup (Steps 1-3): ~5 minutes
- Testing (Steps 4-6): ~2 minutes
- Verification (Steps 7-10): ~3 minutes
- **Total**: ~10 minutes

---

## Success Criteria

The implementation is verified if:
- All 17 tests pass
- No compilation errors
- Off-chain transfers generate 0 blockchain transactions
- Fraud prevention works (test_alice_tries_to_cheat passes)
- All attack vectors are blocked (10 malicious behavior tests pass)
