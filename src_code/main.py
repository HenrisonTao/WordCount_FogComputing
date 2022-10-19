'''Usage: client.py [-h] RUN_MODE SERVER_IP SERVER_PORT

Arguments:
   RUN_MODE  0:CLOUD , 1:FOG , 2:Client
   SERVER_IP  IP of server.
   SERVER_PORT Port of server.
Options:
   -h --help
'''

import queue
import socket
import re
from docopt import docopt
import threading
import heapq
import time
import logging 

Encode_Code="utf8"
FOG_PORT= 5001
CLOUD_PORT=5000
DIFF_WORDS_LIMIT = 5000
LAST_UPDATE_TIMES_LIMIT= 3*60  ## 3 minutes
TOPN_HOTTEST=10
TOPN_HOTTEST_REFRESH_TIME= 30 # 30 seconds
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s : %(message)s' ) 

class client_data_job:
    def __init__(self, client, data):
        self.client = client  
        self.data = data

class socket_class:
    def __init__(self, remote_dst_ip, remote_dst_port , local_port):
        ###  socket setting
        self.Socket_Buffer= 1024
        self.Listen_thread_num = 5

        #### job setting
        self.job_queue = queue.Queue()
        self.remoteIP = remote_dst_ip
        self.remotePort = remote_dst_port
        # self.localIP = "127.0.0.1"
        self.localIP = socket.gethostname()
        self.localPort = local_port


    def TCP_send(self,data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rsp_data = ""
        try:
            s.connect((self.remoteIP, self.remotePort))
            ## 1 : send the length of data
            s.send(bytes(str(len(data)), encoding = Encode_Code) )
            rsp_data = s.recv(self.Socket_Buffer)
            if rsp_data.decode(Encode_Code) == "OK":
                ## 2: send data
                s.send(data.encode(Encode_Code))
                rsp_data = s.recv(self.Socket_Buffer)
                if rsp_data.decode(Encode_Code) == "DONE":
                    # s.send(data.encode(Encode_Code))
                    # rsp_data = s.recv(self.Socket_Buffer)
                    # print("recv data:", rsp_data.decode(Encode_Code))
                    return rsp_data.decode(Encode_Code)
        except socket.error as e:
            print(str(e))
            # logging.ERROR(e)
            return ""
        s.close()
        return ""

    def start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.localIP, self.localPort))
        s.listen(self.Listen_thread_num)
        logging.info("Server started! Wait for connect !")
        while True:
            ## client_address = [ip , port]
            client_connection, client_address = s.accept()
            logging.info('Connection from : ' + client_address[0] + ':' + str(client_address[1]))
            # print('Connection from : ' + client_address[0] + ':' + str(client_address[1]))
            threading.Thread(target=self.on_new_client,args=(client_connection,client_address)).start()

    def on_new_client(self,clientsocket,addr):
        data_len = clientsocket.recv(self.Socket_Buffer)
        current_offest=0
        data_length = int(data_len.decode(Encode_Code))
        logging.info("Server started! Wait for connect !")
        clientsocket.send(bytes("OK", encoding = Encode_Code) )
        data_bytes = bytearray()
        while current_offest < data_length:
            data_bytes += clientsocket.recv(self.Socket_Buffer)
            current_offest = current_offest + self.Socket_Buffer
        clientsocket.send(bytes("DONE", encoding = Encode_Code) )
        #print("addr:",addr,"data:",data_bytes.decode(Encode_Code))
        clientsocket.close()

        ## input job to job_queue
        self.job_queue.put(client_data_job(addr,data_bytes.decode(Encode_Code)))

class Cloud_Wordtalbe_Job:
    def __init__(self,sc:socket_class,TopN:int):
        self.Writer_queue= queue.Queue()
        self.NewClientJob_queue= sc.job_queue
        self.Word_talbe={}
        # self.Hottest_word=[]
        self.TopN=TopN
        
        ## one thread for receive job from fog node and push job to jobqueue 
        threading.Thread(target=sc.start_server).start()

        ## one thread for check new job(from fog) and push update job to writter queue
        threading.Thread(target=self.process_jobQ).start()

        ## one thread for process the wirrter queue
        threading.Thread(target=self.process_writterQ).start()

    def process_jobQ(self):
        while True:
            if self.NewClientJob_queue.qsize()>0:
                job = self.NewClientJob_queue.get()
                logging.info("Process NewClientJob: " + str(job.client[0]))    
                self.str_to_dict(job.data)
            else:
                continue      

    def update_table(self,key,count):
        self.Writer_queue.put([key,count])

    def str_to_dict(self,str_data):
        words = str_data.split(",")
        for word in words:
            # print(word)
            if(word==""):
                break
            word_index,word_count = word.split(":")
            self.update_table(word_index,int(word_count))

    def process_writterQ(self):
        while True:
            if self.Writer_queue.qsize()>0:

                write_job = self.Writer_queue.get()
                word_index =  write_job[0]
                word_count = write_job[1]
                # logging.info("Process WordTable Update: " + write_job[0])    

                if word_index in self.Word_talbe.keys():
                    self.Word_talbe[word_index] = self.Word_talbe[word_index] + word_count
                else:
                    self.Word_talbe[word_index] = word_count

    def find_top_word(self):
        ###using  dict copy to avoid the  iteration on resize dict error 
        wordtables_snapshot=self.Word_talbe.copy()

        topN_set= heapq.nlargest(self.TopN, wordtables_snapshot, key=wordtables_snapshot.get)
        logging.info("num of words:"+str(len(wordtables_snapshot)))
        if len(topN_set) > 0:
            for x in topN_set:
                print(x,":",wordtables_snapshot[x])
            
        # if you want to show all words and counts
        # for key in tmp_wordtable:
        #     print(key,":",tmp_wordtable[key])

class Fog_Word_Job:
    def __init__(self,sc:socket_class):
        self.Word_talbe={}
        self.lastUpdateTime=0
        self.socket_class = sc
        threading.Thread(target=sc.start_server).start()
        threading.Thread(target=self.queue_process).start()

    def queue_process(self):
        while True:
            if sc.job_queue.qsize()>0:
                job = sc.job_queue.get()
                self.update_word_count(self.data_to_word_set(job.data))
            self.check_send2cloud_conditions()

    def send_to_cloud(self):
        send_data=""
        for word in self.Word_talbe:
            send_data += word + ":" + str(self.Word_talbe[word]) + ","
        self.socket_class.TCP_send(send_data)
        self.re_init_Word_table()
        logging.info("Send word_count to cloud!")

    def re_init_Word_table(self):
        self.Word_talbe={}

    def update_word_count(self,words_set):
        for word in words_set:
            ##stored with lowercase word
            word_index = word.lower()
            if word_index in self.Word_talbe:
                self.Word_talbe[word_index] = self.Word_talbe[word_index] + 1  
            else:
                self.Word_talbe[word_index] = 1

    def data_to_word_set(self,data):
        word_set = re.findall(r"(?i)\b[a-z]+\b", data)
        return word_set

    def check_send2cloud_conditions(self):
        word_in_words_set= len(self.Word_talbe) 
        if word_in_words_set > 0 :
            since_of_lasteUpdate_time = time.time() - self.lastUpdateTime
            if since_of_lasteUpdate_time > LAST_UPDATE_TIMES_LIMIT or word_in_words_set > DIFF_WORDS_LIMIT:
                self.send_to_cloud()

if __name__ == '__main__':
    args = docopt(__doc__)

    RUN_MODE = int(args['RUN_MODE'])
    REMOTE_DST_Server_IP =args['SERVER_IP']
    REMOTE_DST_Server_Port= int(args['SERVER_PORT'])

    if RUN_MODE == 0:
        sc = socket_class(None,None,CLOUD_PORT)
        cwj = Cloud_Wordtalbe_Job(sc,TOPN_HOTTEST)
        while True:
            time.sleep(TOPN_HOTTEST_REFRESH_TIME)
            
            logging.info("Refresh Hottest Word!")
            cwj.find_top_word()
            
    elif RUN_MODE== 1 :
        #Fog Node
        sc = socket_class(REMOTE_DST_Server_IP,REMOTE_DST_Server_Port,FOG_PORT)    
        ## start new fog server
        fwj = Fog_Word_Job(sc)

    elif RUN_MODE == 2 :    
        #Client Node
        #client doesnt need to start socket server side 
        sc = socket_class(REMOTE_DST_Server_IP,REMOTE_DST_Server_Port,None)    
        data = ""
        with open('test_data.txt', 'r',encoding=Encode_Code) as f:
            data = f.read()
        sc.TCP_send(data)
        logging.info("send data to FogNode!")

    else:
        logging.ERROR("WRONG RUN_MODE!")