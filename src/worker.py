import queue
from ollama import Client
from src.utils import *
from pathlib import Path
from src.logger import logger

def worker():
    '''
        Worker that processes waiting message
    '''
    while True:
        user_id, text = msg_queue.get()

        if user_id is None:  # shutdown signal
            break
        
        # Call OpenAI
        try:
            ####################### REPLACE THIS BLOCK AFTER GETTING OPENAI KEY #######################
            response = client.chat(model='deepseek-r1:8b', options={'num_predict': 100}, messages=[   #
                {                                                                                     #
                    'role': 'user',                                                                   #
                    'content': text,                                                                  #
                },                                                                                    #
            ])                                                                                        #
            reply = response['message']['content']                                                    #
            ###########################################################################################
        except Exception as e:
            reply = f"Error: {str(e)}"
        
        send_message_to_zalo(user_id, reply, config)
        msg_queue.task_done()


### REPLACE THIS BLOCK AFTER GETTING OPENAI KEY ###
logger.info("Initialize connection to AI Server") #
client = Client(                                  #
  host='http://27.74.240.106:11434'               #
)                                                 #
###################################################

logger.info("Initialize queue")
msg_queue = queue.Queue()
config = load_config()
config = check_zalo_oa_token(config, False)