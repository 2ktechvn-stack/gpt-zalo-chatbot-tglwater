import queue
from src.utils import *
from src.logger import logger
from openai import OpenAI
import re
from datetime import datetime, timedelta
import traceback

def remind_customer(config, remind_script):
    # Get all customer_last_interaction
    customer_last_interactions = get_all_customer_last_interaction()
    
    for customer_last_interaction in customer_last_interactions:
        user_id = customer_last_interaction[0]
        platform = customer_last_interaction[1]
        time = customer_last_interaction[2]
        count = customer_last_interaction[3]

        try:
            if count == 2 and datetime.now() - datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f') >= timedelta(hours=23):
                logger.info('Send 1 day remind to ' + user_id + ' - ' + platform)
                # Send message 1 day
                if platform == 'zalo' and config['REMINDER_ON']:
                    send_message_to_zalo(user_id, remind_script['remind_1_day'], config)
                elif platform == 'fb' and config['REMINDER_ON']:
                    send_message_to_fb(user_id, remind_script['remind_1_day'], config)
                
                # update_customer_last_interaction(user_id, platform, 3)
                delete_customer_last_interaction(user_id, platform)
                    
            elif count == 1 and datetime.now() - datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f') >= timedelta(hours=4):
                logger.info('Send 4 hours remind to ' + user_id + ' - ' + platform)
                # Send message 4 hours
                if platform == 'zalo' and config['REMINDER_ON']:
                    send_message_to_zalo(user_id, remind_script['remind_4_hours'], config)
                elif platform == 'fb' and config['REMINDER_ON']:
                    send_message_to_fb(user_id, remind_script['remind_4_hours'], config)

                update_customer_last_interaction(user_id, platform, 2)

            elif count == 0 and datetime.now() - datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f') >= timedelta(hours=1):
                logger.info('Send 30 minutes remind to ' + user_id + ' - ' + platform)
                # Send message 30 minutes
                if platform == 'zalo' and config['REMINDER_ON']:
                    send_message_to_zalo(user_id, remind_script['remind_1_hour'], config)
                elif platform == 'fb' and config['REMINDER_ON']:
                    send_message_to_fb(user_id, remind_script['remind_1_hour'], config)

                update_customer_last_interaction(user_id, platform, 1)
        except:
            delete_customer_last_interaction(user_id, platform)
        
    msg_queue.put(("", "", "", 'remind', ""))

def worker():
    '''
        Worker để xử lý các tin nhắn trong hàng chờ
    '''

    config = load_config()
    config = check_zalo_oa_token(config, False)
    init_db()
    remind_script = load_remind_script()

    logger.info("Initialize connection to AI Server") 
    client = OpenAI(api_key=config['OPENAI_API_KEY'])

    while True:
        platform, user_id, text, event_name, mid = msg_queue.get()

        if text and check_if_user_send_admin_command(platform, text, user_id, config):
            config = load_config()
            logger.info("User send admin command")

        # Check if user send phone number
        elif text and check_if_user_send_phone_number(platform, text, user_id, config):
            logger.info("User send phone number")

        # Check if employee send message
        elif event_name == 'oa_send_text':
            logger.info("Update time created")
            update_time_created(platform, user_id)

        elif event_name == 'fb_echo':
            # Check if recent_reply_message_id != mid
            try:
                logger.info('FB echo')
                recent_reply_message_id = get_recent_reply_message_id(platform, user_id)
                if recent_reply_message_id != mid:
                    logger.info('Update time created')
                    update_time_created(platform, user_id)
                else:
                    logger.info('Do nothing')
            except Exception as e:
                logger.error(traceback.format_exc())

        elif event_name == 'remind':
            try:
                remind_customer(config, remind_script)
            except Exception as e:
                logger.error(traceback.format_exc())

        # Call OpenAI
        elif event_name == 'user_send_text':
            try:
                # Check if user_id has in database, if not, create thread and insert
                if not get_threads(user_id, platform):
                    thread = client.beta.threads.create()
                    logger.info(f"Create thread id {thread.id} for user {user_id}")
                    save_thread(platform, thread.id, user_id)

                # Check if user_id in user_phone_number, if not continue, else task done
                if get_user_phone_number(user_id):
                    msg_queue.task_done()
                    continue
                
                # Check if user_id has in customer_last_interaction, if not, insert
                customer_last_interaction = get_customer_last_interaction(user_id, platform)
                if not customer_last_interaction and config['REMINDER_ON']:
                    insert_customer_last_interaction(user_id, platform)
                elif customer_last_interaction and config['REMINDER_ON']:
                    update_customer_last_interaction(user_id, platform)
                
                thread = get_threads(user_id, platform)
                # logger.info(thread)

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
                reply = re.sub(r"【.*?】", " ", reply)

                # Normalize spaces (avoid double spaces after removal)
                reply = re.sub(r"\s{2,}", " ", reply).strip()

                if platform == 'zalo':
                    send_message_to_zalo(user_id, reply, config)
                elif platform == 'fb':
                    mid = send_message_to_fb(user_id, reply, config)
                    update_recent_reply_message_id(platform, user_id, mid)

            except Exception as e:
                reply = traceback.format_exc()
                logger.error(reply)
            
        msg_queue.task_done()
            

logger.info("Initialize queue")
msg_queue = queue.Queue()
msg_queue.put(("", "", "", 'remind', ""))