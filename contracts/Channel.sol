//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ChannelInterface.sol";

contract Channel is ChannelI {
    // This contract will be deployed every time we establish a new payment channel between two participant.
    // The creator of the channel also injects funds that can be sent (and later possibly sent back) in this channel

    address payable public party1;
    address payable public party2;
    uint public totalDeposit;
    uint public appealPeriodLen;
    
    bool public channelClosed;
    uint public closureTime;
    uint public balance1;
    uint public balance2;
    uint public currentSerialNum;
    
    mapping(address => bool) public withdrawn;

    event ChannelClosed(uint balance1, uint balance2, uint serialNum);
    event AppealMade(uint balance1, uint balance2, uint serialNum);
    event FundsWithdrawn(address party, uint amount);

    function _verifySig(
        // Do not change this function!
        address contract_address,
        uint _balance1,
        uint _balance2,
        uint serialNum, //<--- the message
        uint8 v,
        bytes32 r,
        bytes32 s, // <---- The signature
        address signerPubKey
    ) public pure returns (bool) {
        // v,r,s together make up the signature.
        // signerPubKey is the public key of the signer
        // contract_address, _balance1, _balance2, and serialNum constitute the message to be signed.
        // returns True if the sig checks out. False otherwise.

        // the message is made shorter:
        bytes32 hashMessage = keccak256(
            abi.encodePacked(contract_address, _balance1, _balance2, serialNum)
        );

        //message signatures are prefixed in ethereum.
        bytes32 messageDigest = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hashMessage)
        );
        //If the signature is valid, ecrecover ought to return the signer's pubkey:
        return ecrecover(messageDigest, v, r, s) == signerPubKey;
    }

    constructor(address payable _otherOwner, uint _appealPeriodLen) payable {
        party1 = payable(msg.sender);
        party2 = _otherOwner;
        totalDeposit = msg.value;
        appealPeriodLen = _appealPeriodLen;
        channelClosed = false;
    }

    function oneSidedClose(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(!channelClosed, "Channel already closed");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        
        if (serialNum == 0) {
            balance1 = totalDeposit;
            balance2 = 0;
            currentSerialNum = 0;
        } else {
            require(_balance1 + _balance2 == totalDeposit, "Invalid balances");
            address signer = (msg.sender == party1) ? party2 : party1;
            require(_verifySig(address(this), _balance1, _balance2, serialNum, v, r, s, signer), "Invalid signature");
            
            balance1 = _balance1;
            balance2 = _balance2;
            currentSerialNum = serialNum;
        }
        
        channelClosed = true;
        closureTime = block.timestamp;
        emit ChannelClosed(balance1, balance2, currentSerialNum);
    }

    function appealClosure(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(channelClosed, "Channel not closed");
        require(block.timestamp < closureTime + appealPeriodLen, "Appeal period over");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        require(serialNum > currentSerialNum, "Serial number not higher");
        require(_balance1 + _balance2 == totalDeposit, "Invalid balances");
        
        address signer = (msg.sender == party1) ? party2 : party1;
        require(_verifySig(address(this), _balance1, _balance2, serialNum, v, r, s, signer), "Invalid signature");
        
        balance1 = _balance1;
        balance2 = _balance2;
        currentSerialNum = serialNum;
        emit AppealMade(balance1, balance2, serialNum);
    }

    function withdrawFunds(address payable destAddress) external {
        require(channelClosed, "Channel not closed");
        require(block.timestamp >= closureTime + appealPeriodLen, "Appeal period not over");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        require(!withdrawn[msg.sender], "Already withdrawn");
        
        uint amount = (msg.sender == party1) ? balance1 : balance2;
        withdrawn[msg.sender] = true;
        
        emit FundsWithdrawn(msg.sender, amount);
        destAddress.transfer(amount);
    }

    function getBalance() external view returns (uint) {
        require(channelClosed, "Channel not closed");
        require(block.timestamp >= closureTime + appealPeriodLen, "Appeal period not over");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        
        return (msg.sender == party1) ? balance1 : balance2;
    }
}
