import queue
from src.utils import *
from src.logger import logger
from openai import OpenAI
import re
from datetime import datetime, timedelta
import traceback

def worker():
    '''
        Worker that processes waiting message
    '''

    config = load_config()
    config = check_zalo_oa_token(config, False)
    init_db()

    logger.info("Initialize connection to AI Server") 
    client = OpenAI(api_key=config['OPENAI_API_KEY'])

    while True:
        platform, user_id, text, event_name = msg_queue.get()
        logger.info('Get message from queue')

        if user_id is None:  # shutdown signal
            break

        if check_if_user_send_admin_command(platform, text, user_id, config):
            logger.info("User send admin command")

        # Check if user send phone number
        elif check_if_user_send_phone_number(platform, text, user_id, config):
            logger.info("User send phone number")

        # Check if employee send message
        elif event_name == 'oa_send_text':
            logger.info("Update time created")
            update_time_created(platform, user_id)

        # Call OpenAI
        else:
            try:
                # Check if user_id has in database, if not, create thread and insert
                if not get_threads(user_id, platform):
                    thread = client.beta.threads.create()
                    logger.info(f"Create thread id {thread.id} for user {user_id}")
                    save_thread(platform, thread.id, user_id)
                
                thread = get_threads(user_id, platform)
                logger.info(thread)

                # Search for time_created in threads database, if now - time_created <= STOP_CHAT_WHEN_INTERRUPT_IN, continue the loop
                if datetime.now() - datetime.strptime(thread[0][2], '%Y-%m-%dT%H:%M:%S.%f') <= timedelta(minutes=int(config['STOP_CHAT_WHEN_INTERRUPT_IN'])):
                    msg_queue.task_done()
                    continue

                # Get thread_id from database
                thread_id = thread[0][0]
                
                logger.info('Create message object')
                message = client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role='user',
                    content=text
                )
                
                logger.info("Get response")
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread_id, assistant_id=config['ASSISTANT_ID']
                )

                messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
                message_content = messages[0].content[0].text

                reply = message_content.value
                reply = re.sub(r"\s*\[\d+\]\s*", " ", reply)

                # Normalize spaces (avoid double spaces after removal)
                reply = re.sub(r"\s{2,}", " ", reply).strip()

                if platform == 'zalo':
                    send_message_to_zalo(user_id, reply, config)
                elif platform == 'fb':
                    send_message_to_fb(user_id, reply, config)

            except Exception as e:
                reply = traceback.format_exc()
                logger.error(reply)
            
        msg_queue.task_done()
            

logger.info("Initialize queue")
msg_queue = queue.Queue()