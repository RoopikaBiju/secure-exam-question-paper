const { ethers } = require("ethers");

const provider = new ethers.JsonRpcProvider("http://127.0.0.1:7545");

if (!process.env.PRIVATE_KEY || !process.env.CONTRACT_ADDRESS) {
  throw new Error("Blockchain env variables not set");
}

const privateKey = process.env.PRIVATE_KEY;
const wallet = new ethers.Wallet(privateKey, provider);

const contractAddress = process.env.CONTRACT_ADDRESS;

const abi = [
  "function storePaper(string paperId, string hash, uint examTime) public",
  "function getPaper(string paperId) public view returns (string, uint)"
];

const contract = new ethers.Contract(contractAddress, abi, wallet);

async function storePaperOnChain(paperId, hash, examTime) {
  const tx = await contract.storePaper(paperId, hash, examTime);
  await tx.wait();
  console.log("Paper hash stored on blockchain");
}

async function getPaperFromChain(paperId) {
  return await contract.getPaper(paperId);
}

module.exports = {
  storePaperOnChain,
  getPaperFromChain
};