# cryptocurrency

This project is focused on creating a new cryptocurrency 



run it by typing: python node.py --port <port_number>
then go to localhost:<port_number> to manage the blockchain








blockchain architecture:
-----------------------

* each user must sustain a node and connect to other peers
* a wallet is the RSA encryption keys, the private key must remain hidden to other users  
* transaction is the way to send and receive coin, each transaction contains indo about the sender, recepient, amount and etc
* each transaction is signed by the sender (to confirm it was sent by him)
* to make a transaction valid among the net, it must be mined
* mining is when a miner searches for a combination upon the open trasactions to provide a proof of work
* a block is a list of valid transaction with some exttra data (such as the proof of work), each blovk is hashed with the previous block hash, so it's impossible to change the blockchain backwards
* a blockchain is a list of blocks








