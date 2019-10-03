# cryptocurrency

This project is focused on creating a new cryptocurrency 



run it by typing: python node.py --port <port_number>
then go to localhost:<port_number> to manage the blockchain








blockchain architecture:
-----------------------

* Each user must sustain a node and connect to other peers.
* A wallet is the RSA encryption keys, the private key must remain hidden from users.
* Transaction is the way to send and receive coin, each transaction contains info about the sender, recepient, amount and etc.
* Each transaction is signed by the sender (to confirm it was sent by him).
* To make a transaction valid among the net, it must be mined.
* Mining is when a miner searches for a combination upon the open trasactions to provide a proof of work.
* A block is a list of valid transaction with some extra data (such as the proof of work), each block is hashed with the previous block     hash, so it's impossible to change the blockchain farward.
* A blockchain is a list of blocks.
* When adding new peers, the peers with the longest blockchain wins and it spreads upon all the connected nodes. 






