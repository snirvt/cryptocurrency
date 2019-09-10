from collections import OrderedDict

from utility.printable import Printable


class Transaction(Printable):
    """A transaction which can be added to a block in the blockchain.

    Attributes:
        :sender: The sender of the coins.
        :recipient: The recipient of the coins.
        :signature: The signature of the transaction.
        :amount: The amount of coins sent.
    """

    def __init__(self, sender, recipient, signature, amount, time):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.time = time
        self.signature = signature

    def to_ordered_dict(self):
        """Converts this transaction into a (hashable) OrderedDict."""
        return OrderedDict([('sender', self.sender),
                            ('recipient', self.recipient),
                            ('amount', self.amount),
                            ('time', self.time)])
    @staticmethod
    def to_transaction_from_dict(transaction):
        return Transaction(transaction['sender'],
        transaction['recipient'],
        transaction['signature'],
        transaction['amount'],
        transaction['time'])

    @staticmethod
    def contains_transaction(transactionsList, transaction):
        for tx in transactionsList:
            if Transaction.compare_transactions(tx, transaction):
                return True
        return False

    @staticmethod
    def compare_transaction_containers(txList1, txList2):
        list_1_Length = len(txList1)
        list_2_Length = len(txList2)
        if list_1_Length is not list_2_Length:
            return False
        for i in range(list_1_Length):
            if not Transaction.compare_transactions(txList1[i], txList2[i]):
                return False
        return True
    
    
    @staticmethod
    def compare_transactions_list(txList1, txList2):
        len1 = len(txList1)
        len2 = len(txList2)

        if len1 is not len2:
            return False

        for i in range(len1):
            if not Transaction.compare_transactions(txList1[i], txList2[i]):
                return False
        return True

    @staticmethod
    def compare_transactions(tx1,tx2):
        # print(tx1)
        # print(tx2)
        # print(type(tx1))
        # print(type(tx2))

        if(tx1.sender == tx2.sender and 
            tx1.recipient == tx2.recipient and 
            tx1.signature == tx2.signature and 
            tx1.amount == tx2.amount and
            tx1.time == tx2.time):
                return True

            
        