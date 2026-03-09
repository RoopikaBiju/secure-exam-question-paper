// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ExamPaper {

    // Who deployed this contract (University admin)
    address public admin;

    struct Paper {
        string  ipfsHash;          // Where the encrypted paper is stored
        bytes32 paperHash;         // SHA256 of original paper (for integrity)
        uint256 unlockTime;        // Unix timestamp of exam start
        string  encryptedKey;      // AES key, encrypted with admin's public key
        bool    isReleased;        // Has the key been released?
        string  examName;
    }

    // examId => Paper
    mapping(uint256 => Paper) public papers;
    uint256 public paperCount;

    // Events - logged on blockchain permanently
    event PaperUploaded(uint256 examId, string examName, uint256 unlockTime);
    event KeyReleased(uint256 examId, string decryptionKey);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can do this");
        _;
    }

    modifier examTimeReached(uint256 examId) {
        require(block.timestamp >= papers[examId].unlockTime, 
                "Exam time not reached yet");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    // Called when paper is ready (before exam)
    function uploadPaper(
        string memory _ipfsHash,
        bytes32 _paperHash,
        uint256 _unlockTime,
        string memory _encryptedKey,
        string memory _examName
    ) public onlyAdmin {
        require(_unlockTime > block.timestamp, "Unlock time must be in future");

        papers[paperCount] = Paper({
            ipfsHash:     _ipfsHash,
            paperHash:    _paperHash,
            unlockTime:   _unlockTime,
            encryptedKey: _encryptedKey,
            isReleased:   false,
            examName:     _examName
        });

        emit PaperUploaded(paperCount, _examName, _unlockTime);
        paperCount++;
    }

    // Called AT exam time - releases decryption key publicly
    function releaseKey(uint256 examId) 
        public 
        onlyAdmin 
        examTimeReached(examId) 
    {
        require(!papers[examId].isReleased, "Key already released");
        papers[examId].isReleased = true;

        // This gets permanently recorded on blockchain
        emit KeyReleased(examId, papers[examId].encryptedKey);
    }

    // Anyone can verify if paper was tampered with
    function verifyPaper(uint256 examId, bytes32 hashToCheck) 
        public view returns (bool) 
    {
        return papers[examId].paperHash == hashToCheck;
    }

    // Get paper details (encrypted key only visible after release)
    function getPaper(uint256 examId) 
        public view returns (
            string memory, bytes32, uint256, bool, string memory
        ) 
    {
        Paper memory p = papers[examId];
        return (p.ipfsHash, p.paperHash, p.unlockTime, p.isReleased, p.examName);
    }


    // Add this event at the top with other events
event UnlockTimeUpdated(uint256 examId, uint256 newUnlockTime);

    // Add this function before the closing brace
    function updateUnlockTime(uint256 examId, uint256 newUnlockTime)
        public
        onlyAdmin
    {
        require(!papers[examId].isReleased, "Cannot change time after key is released");
        require(newUnlockTime > block.timestamp, "New time must be in the future");
        papers[examId].unlockTime = newUnlockTime;
        emit UnlockTimeUpdated(examId, newUnlockTime);
    }

}