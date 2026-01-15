const CryptoJS = require("crypto-js");

if (!process.env.AES_SECRET_KEY) {
  throw new Error("AES_SECRET_KEY not set");
}

const SECRET_KEY = process.env.AES_SECRET_KEY

function encrypt(text){
  return CryptoJS.AES.encrypt(text, SECRET_KEY).toString();
}

function decrypt(cipher){
  const bytes = CryptoJS.AES.decrypt(cipher, SECRET_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}

module.exports = { encrypt, decrypt };
