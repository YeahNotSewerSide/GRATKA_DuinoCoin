import requests
import datetime
import threading
import Graph


STANDART_WHITE_LIST = ['coinexchange',
                       'NodeSBroker',
                       'NodeS',
                       'ducofaucet',
                       'exchange-bot',
                       'revox']

class Transaction:
    def __init__(self,hash:str,raw_data:dict):
        self.amount:float = raw_data['amount']
        self.sender:str = raw_data['sender']
        self.recipient:str = raw_data['recipient']
        self.hash:str = hash
        self.datetime:int = int(datetime.datetime.strptime(raw_data['datetime'],
                                                        "%d/%m/%Y %H:%M:%S").timestamp())
    def __str__(self):
        return f"[{self.datetime}]: {self.sender} -> {self.recipient} | {self.amount} | {self.hash}"
    def __repr__(self):
        return f"{self.sender} -> {self.recipient} | {self.amount}"
    def __eq__(self,tr):
        return self.hash == tr.hash
    def __lt__(self,tr):
        return self.datetime < tr.datetime
    def __le__(self,tr):
        return self.datetime <= tr.datetime
    def __ge__(self,tr):
        return self.datetime >= tr.datetime
       
    def get_sender(self):
        return self.sender
    def get_recipient(self):
        return self.recipient
        
class TrasnsactionsChain:
    '''Main class for working with connected transactions'''
    def __init__(self, root_username, transactions=[], sort = True):
        self.transactions = transactions
        self.sort = sort
        self.root_username = root_username
        if sort:
            self._sort_transactions()

        self.graph = None
        
    def _binary_search(self,transaction:Transaction, start:int, end:int) -> int:
        if start >= end:
            if end<len(self.transactions) and self.transactions[end] > transaction:
                return end
            else:
                return end+1       

        half_start = start + ((end-start)>>1)
        if transaction < self.transactions[half_start]:
            return self._binary_search(transaction, start, half_start-1)
        elif transaction > self.transactions[half_start]:
            return self._binary_search(transaction, half_start+1, end)
        else:
            return half_start
            
    def _sort_transactions(self):
        def sorting_criteria(element:Transaction):
            return element.datetime
        self.transactions.sort(key=sorting_criteria)
        
    def _search_transaction_by_hash(self, hash:str) -> Transaction:
        for transaction in self.transactions:
            if transaction.hash == hash:
                return transaction
                
    def append_transaction(self, transaction:Transaction, ensure_no_copy=True):
        if len(self.transactions) == 0:
            self.transactions.append(transaction)
            return
        if self.sort:
            index = self._binary_search(transaction,0,len(self.transactions))
            if ensure_no_copy:
                first_half = self.transactions[:index]
                for tr in first_half[::-1]:
                    if tr.datetime != transaction.datetime:
                        break
                    if tr.hash == transaction.hash:
                        return

                second_half = self.transactions[index:]
                for tr in second_half:
                    if tr.datetime != transaction.datetime:
                        break
                    if tr.hash == transaction.hash:
                        return
            self.transactions.insert(index,transaction)
        else:
            if self[transaction.hash] == None:
                self.transactions.append(transaction)
    
    def __getitem__(self, key):
        if isinstance(key,int):
            return self.transactions[key]
        elif isinstance(key,str):
            return self._search_transaction_by_hash(key)
    def __str__(self):
        to_return = ''
        for transaction in self.transactions[:-1]:
            to_return += str(transaction) + '\n'
        try:
            to_return += str(transactions[-1])
        except:
            pass
        return to_return
    def __repr__(self):
        for transaction in self.transactions:
            print(transaction.__repr__)

    def search_transactions_by_recipient(self, username:str) -> list:
        to_return = []
        for transaction in self.transactions:
            if transaction.recipient == username:
                to_return.append(transaction)
        return to_return

    def search_transactions_by_sender(self, username:str) -> list:
        to_return = []
        for transaction in self.transactions:
            if transaction.sender == username:
                to_return.append(transaction)
        return to_return

    def get_top_senders(self, recipient_username = None, top = 10):
        '''returns list[sender_username, amount_sent]'''
        if recipient_username == None:
            recipient_username = self.root_username
        amounts = [] # [username,amount]
        lookup_table = {} # username:index
        transactions = self.search_transactions_by_recipient(recipient_username)
        for transaction in transactions:
            index = lookup_table.get(transaction.get_sender(),len(amounts))
            if index == len(amounts):
                amounts.append([transaction.get_sender(),0.0])
                lookup_table[transaction.get_sender()] = index
            amounts[index][1] += transaction.amount
        def sorting_criteria(element):
            return element[-1]
        amounts.sort(reverse=True, key=sorting_criteria)
        return amounts[:top]

    def get_top_recipients(self, sender_username = None, top = 10):
        '''returns list[recipient_username, amount_recieved_from_sender]'''
        if sender_username == None:
            sender_username = self.root_username
        amounts = [] # [username,amount]
        lookup_table = {} # username:index
        transactions = self.search_transactions_by_sender(sender_username)
        for transaction in transactions:
            index = lookup_table.get(transaction.get_recipient(),len(amounts))
            if index == len(amounts):
                amounts.append([transaction.get_recipient(),0.0])
                lookup_table[transaction.get_recipient()] = index
            amounts[index][1] += transaction.amount

        def sorting_criteria(element):
            return element[-1]
        amounts.sort(reverse=True, key=sorting_criteria)
        return amounts[:top]
    
    def search_one_way_senders(self, recipient=None) -> list:
        if recipient == None:
            recipient = self.root_username
        recieved_transactions = self.search_transactions_by_recipient(recipient)
        #sent_by_recipient_transactions = self.search_transactions_by_sender(recipient)
        processed_senders = {} # username:True
        to_return = []

        for transaction in recieved_transactions:
            if transaction.get_sender() in processed_senders:
                continue
            else:
                processed_senders[transaction.get_sender()] = True

            only_one_recipient = 1
            only_sending = 1
            same_recipient_sender = 1

            recieved_by_sender_transactions = self.search_transactions_by_recipient(transaction.get_sender())
            if len(recieved_by_sender_transactions) > 0:
                only_sending = 0

            count_fails = 1
            count_passes = 1
            for recieved_transaction in recieved_by_sender_transactions:
                if recieved_transaction.get_sender() == recipient:
                    count_fails += 1
                else:
                    count_passes += 1
            #same_recipient_sender = count_fails//count_passes
            if count_fails >= count_passes:
                same_recipient_sender = 1

            count_fails = 1
            count_passes = 1
            sent_transactions = self.search_transactions_by_sender(transaction.get_sender())
            for sent_transaction in sent_transactions:
                if sent_transaction.get_recipient() != recipient:
                    count_passes += 1
                else:
                    count_fails += 1
            #only_one_recipient = count_fails//count_passes
            if count_fails >= count_passes:
                only_one_recipient = 1
            
            if only_one_recipient + only_sending + same_recipient_sender >= 2:
                to_return.append(transaction.get_sender())   
                
        return to_return


    def search_one_way_recipients(self, sender = None) -> list:
        if sender == None:
            sender = self.root_username
        sent_by_recipient_transactions = self.search_transactions_by_sender(sender)
        processed_recipients = {} # username:True
        to_return = []

        for transaction in sent_by_recipient_transactions:
            if transaction.get_recipient() in processed_recipients:
                continue
            else:
                processed_recipients[transaction.get_recipient()] = True

            only_one_recipient = 1
            only_recieving = 1
            same_recipient_sender = 1

            sent_by_reciever_transactions = self.search_transactions_by_sender(transaction.get_recipient())
            if len(sent_by_reciever_transactions) > 0:
                only_recieving = 0
            
            recieved_by_reciever_transactions = self.search_transactions_by_recipient(transaction.get_recipient())

            count_fails = 1
            count_passes = 1
            for recieved_transaction in recieved_by_reciever_transactions:
                if recieved_transaction.get_sender() == sender:
                    count_fails += 1
                else:
                    count_passes += 1
            #same_recipient_sender = count_fails//count_passes
            if count_fails >= count_passes:
                same_recipient_sender = 1

            count_fails = 1
            count_passes = 1
            sent_transactions = self.search_transactions_by_sender(transaction.get_sender())
            for sent_transaction in sent_transactions:
                if sent_transaction.get_recipient() != sender:
                    count_passes += 1
                else:
                    count_fails += 1
            #only_one_recipient = count_fails//count_passes
            if count_fails >= count_passes:
                only_one_recipient = 1
            
            if only_one_recipient + only_recieving + same_recipient_sender >= 2:
                to_return.append(transaction.get_recipient())   
                
        return to_return

    def total_recieved(self, username=None) -> float:
        if username == None:
            username = self.root_username
        transactions = self.search_transactions_by_recipient(username)
        to_return = 0.0
        for transaction in transactions:
            to_return += transaction.amount
        return to_return

    def total_sent(self, username=None) -> float:
        if username == None:
            username = self.root_username
        transactions = self.search_transactions_by_sender(username)
        to_return = 0.0
        for transaction in transactions:
            to_return += transaction.amount
        return to_return

    def is_suspicious(self, username = None) -> bool:
        if username == None:
            username = self.root_username
        return self.total_recieved(username) > self.total_sent(username)

    '''GRAPH FUNCTIONS'''
    def get_nodes(self) -> list:
        unique_usernames = {}
        for transaction in self.transactions:
            if transaction.get_sender() not in unique_usernames:
                unique_usernames[transaction.get_sender()] = True
            if transaction.get_recipient() not in unique_usernames:
                unique_usernames[transaction.get_recipient()] = True
        return list(unique_usernames.keys())

    def create_graph(self):
        '''
        0 - no connection
        1 - sender
        2 - reciever
        3 - all connections
        '''
        nodes = self.get_nodes()
        nodes_index_lookup_table = {}
        nodes_amount = len(nodes)
        connection_matrix = []
        weights = []
        for i in range(nodes_amount):
            connection_matrix.append([0]*nodes_amount)
            weights.append([0]*nodes_amount)
            nodes_index_lookup_table[nodes[i]] = i

        for transaction in self.transactions:
            sender_index = nodes_index_lookup_table[transaction.get_sender()]
            recipient_index = nodes_index_lookup_table[transaction.get_recipient()]
            if connection_matrix[sender_index][recipient_index] == 0:
                connection_matrix[sender_index][recipient_index] = 1
            elif connection_matrix[sender_index][recipient_index] == 2:
                connection_matrix[sender_index][recipient_index] = 3

            if connection_matrix[recipient_index][sender_index] == 0:
                connection_matrix[recipient_index][sender_index] = 2
            elif connection_matrix[recipient_index][sender_index] == 1:
                connection_matrix[recipient_index][sender_index] = 3

            weights[sender_index][recipient_index] += 1
            weights[recipient_index][sender_index] += 1
        
        self.graph = Graph.Graph(connection_matrix,nodes,weights)
        return self.graph





        
def get_transactions(username:str) -> list:
    '''gets transactions for 1 user'''

    while True:
        try:
            transactions_json = requests.get(
                f"https://server.duinocoin.com:5000/transactions?username={username}").json()
            break
        except:
            pass
    to_return = []
    for hash,transaction in transactions_json['result'].items():
        to_return.append(Transaction(hash,transaction))
    return to_return

def _get_transactions_threads_handler(username:str, buffer:list):    
    results = get_transactions(username)
    for result in results:
        buffer.append(result)

def _get_transactions_threads_master(usernames:list) -> list:
    buffer = []
    threads_pool = []
    for username in usernames:
        threads_pool.append(threading.Thread(target = _get_transactions_threads_handler,
                                        name = f'{username} getter',
                                        args = (username,buffer)))
    for thread in threads_pool:
        thread.start()
    for thread in threads_pool:
        thread.join()
    return buffer
    
 
def trace_transactions(username:str,
                       white_list=[],
                       use_threads = True, 
                       max_bunch = 10) -> TrasnsactionsChain:
    '''
    traces all transactions for username and all related transactions
    '''
    usernames_to_skip = {}
    for username_to_skip in white_list:
        usernames_to_skip[username_to_skip] = True

    transactions_chain = TrasnsactionsChain(username)
    processed_usernames = {} # username:True
    usernames_to_process = [username]
    
    if not use_threads:
        while len(usernames_to_process) > 0:
            username = usernames_to_process.pop(0)
            transactions = get_transactions(username)
            processed_usernames[username] = True
            for transaction in transactions:
                if transaction.get_sender() not in processed_usernames\
                        and transaction.get_sender() not in usernames_to_process\
                        and transaction.get_sender() not in usernames_to_skip:
                    usernames_to_process.append(transaction.get_sender())
                elif transaction.get_recipient() not in processed_usernames\
                        and transaction.get_recipient() not in usernames_to_process\
                        and transaction.get_recipient() not in usernames_to_skip:
                    usernames_to_process.append(transaction.get_recipient())
                
                transactions_chain.append_transaction(transaction)
    else:
        while len(usernames_to_process) > 0:
            if len(usernames_to_process) == 0:
                username = usernames_to_process.pop(0)
                transactions = get_transactions(username)
                processed_usernames[username] = True
            elif max_bunch == -1 or len(usernames_to_process) < max_bunch:
                transactions = _get_transactions_threads_master(usernames_to_process)
                for username in usernames_to_process:
                    processed_usernames[username] = True
                usernames_to_process = []
            else:
                usernames = usernames_to_process[:max_bunch]
                usernames_to_process = usernames_to_process[max_bunch:]
                transactions = _get_transactions_threads_master(usernames)
                for username in usernames:
                    processed_usernames[username] = True

            
            for transaction in transactions:
                if transaction.get_sender() not in processed_usernames\
                        and transaction.get_sender() not in usernames_to_process\
                        and transaction.get_sender() not in usernames_to_skip:
                    usernames_to_process.append(transaction.get_sender())
                elif transaction.get_recipient() not in processed_usernames\
                        and transaction.get_recipient() not in usernames_to_process\
                        and transaction.get_recipient() not in usernames_to_skip:
                    usernames_to_process.append(transaction.get_recipient())
                
                transactions_chain.append_transaction(transaction)
    return transactions_chain

def total_recieved(username:str) -> float:
    to_return = 0.0
    transactions = get_transactions(username)
    for transaction in transactions:
        if transaction.get_recipient() == username:
            to_return += transaction.amount
    return to_return

def total_sent(username:str) -> float:
    to_return = 0.0
    transactions = get_transactions(username)
    for transaction in transactions:
        if transaction.get_sender() == username:
            to_return += transaction.amount
    return to_return

def determine_main_account(transactions:TrasnsactionsChain,
                          suspicious_accounts:list):
    '''returns list with deterined main accounts'''
    to_return = [] 
    max_amount_transactions = 0
    max_amount_duco = 0
    for sus in suspicious_accounts:
        suspicious_transactions = transactions.search_transactions_by_recipient(sus)
        suspicious_amount = transactions.total_recieved()

        if len(to_return) > 0:
            if (len(suspicious_transactions) > max_amount_transactions\
                    and suspicious_amount > max_amount_duco)\
                    or (len(suspicious_transactions) == max_amount_transactions\
                    and suspicious_amount > max_amount_duco)\
                    or (len(suspicious_transactions) > max_amount_transactions\
                    and suspicious_amount == max_amount_duco):
                to_return = [sus]
                max_amount_transactions = len(suspicious_transactions)
                max_amount_duco = suspicious_amount
            elif len(suspicious_transactions) == max_amount_transactions\
                            and suspicious_amount == max_amount_duco:
                to_return.append(sus)
        else:
            to_return.append(sus)
            max_amount_transactions = len(suspicious_transactions)
    return to_return

def detect_suspicious_accounts(username:str,
                               white_list=[],
                               transactions:list=None,
                               **kwargs) -> tuple:
    '''returns tuple(sus_accounts:list, main_accounts:list)'''

    if transactions == None:
        transactions = trace_transactions(username,white_list,kwargs)

    processed_usernames = {}
    sus_usernames = {username:True}

    sus_accounts = transactions.search_one_way_senders()
    for sus in sus_accounts:
        if sus not in sus_usernames\
            and sus not in white_list:
            sus_usernames[sus] = True

    sus_accounts = transactions.search_one_way_recipients()
    for sus in sus_accounts:
        if sus not in sus_usernames\
            and sus not in white_list:
            sus_usernames[sus] = True

    processed_usernames[username] = True

    for transaction in transactions:
        if transaction.get_sender() not in processed_usernames:
            sus_accounts = transactions.search_one_way_senders(transaction.get_sender())
            for sus in sus_accounts:
                if sus not in sus_usernames\
                    and sus not in white_list:
                    sus_usernames[sus] = True

            sus_accounts = transactions.search_one_way_recipients(transaction.get_sender())
            for sus in sus_accounts:
                if sus not in sus_usernames\
                    and sus not in white_list:
                    sus_usernames[sus] = True

            processed_usernames[transaction.get_sender()] = True
        if transaction.get_recipient() not in processed_usernames:
            sus_accounts = transactions.search_one_way_senders(transaction.get_recipient())
            for sus in sus_accounts:
                if sus not in sus_usernames\
                    and sus not in white_list:
                    sus_usernames[sus] = True
            processed_usernames[transaction.get_recipient()] = True
    sus_usernames = list(sus_usernames.keys())
    main_account = determine_main_account(transactions,sus_usernames)
    return sus_usernames, main_account



if __name__ == '__main__':
    username = 'nzangel'
    transactions = trace_transactions(username,
                                      white_list=STANDART_WHITE_LIST,
                                      max_bunch=-1)
    file = open('output.txt','w',encoding='utf-8')
    file.write(str(transactions))
    file.close()
    print('Senders:')
    print(transactions.get_top_senders(username))
    print('Recievers:')
    print(transactions.get_top_recipients(username))
    #print(total_recieved(username))
    #print(total_sent(username))
    #print(transactions.search_one_way_senders())
    sus = detect_suspicious_accounts(username,
                                     white_list=STANDART_WHITE_LIST,
                                     transactions=transactions,
                                     max_bunch=-1)
    
    print("SUS accounts:",sus[0])
    print("Possible master accounts:",sus[1])
    
    #graph = transactions.create_graph()
    #rout = graph.find_shortest_sending_rout('navair130',username)
    #print('Found correlation rout:')
    #print(" -> ".join(rout))

    #rout = graph.find_strongest_correlations('navair130',username)
    #print('Found strongest correlation:')
    #print(" -> ".join(rout))

    input()
        
    
    
                
    
        