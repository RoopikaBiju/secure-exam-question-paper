// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ExamPaperStorage {

    struct Paper {
        string hash;
        uint examTime;
        bool exists;
    }

    mapping(string => Paper) private papers;

    event PaperStored(string paperId, uint examTime);

    function storePaper(
        string memory paperId,
        string memory hash,
        uint examTime
    ) public {
        require(!papers[paperId].exists, "Paper already stored");
        require(bytes(hash).length > 0, "Invalid hash");
        require(examTime > block.timestamp, "Exam time must be in future");

        papers[paperId] = Paper(hash, examTime, true);
        emit PaperStored(paperId, examTime);
    }

    function getPaper(string memory paperId)
        public
        view
        returns (string memory, uint)
    {
        require(papers[paperId].exists, "Paper not found");
        return (papers[paperId].hash, papers[paperId].examTime);
    }
}
