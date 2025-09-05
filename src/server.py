from flask import Flask, request, jsonify, render_template
import threading
from src.worker import worker, msg_queue, load_config
from src.utils import *
from src.logger import logger

# Chạy worker trong process riêng
threading.Thread(target=worker, daemon=True).start()

app = Flask(__name__)

# Webhook for Zalo
@app.route("/", methods=['POST'])
def webhook():
    # Nhận user id và tin nhắn
    data = request.get_json()
    logger.info(data)
    event_name = data['event_name']

    if event_name in ['user_send_text', 'anonymous_send_text']:
        try:
            user_id = data['sender']['id']

            ### Only send to dev, remove in production ###
            # if user_id not in ['8174221521790538039', '2656106822398634139']:
            #     logger.info("Return 200 OK")
            #     return 'OK', 200
            # logger.info("user is dev")
            ##############################################
            
            message = data['message']['text']

            # Đem vào hàng chờ để đảm bảo thời gian phản hồi theo yêu cầu của Zalo
            msg_queue.put(('zalo', user_id, message, event_name))
            logger.info("Put message to queue")
        except Exception as e:
            logger.error(e)
            raise e
    elif event_name == 'oa_send_text':
        if 'admin_id' in data['sender']:
            user_id = data['recipient']['id']
            msg_queue.put(('zalo', user_id, None, event_name))
            logger.info("Put message to queue")
    else:
        logger.info('Event name not in [user_send_text, anonymous_send_text, oa_send_text]')

    logger.info("Return 200 OK")
    return 'OK', 200

@app.route('/zalo_verifierJ8BkCwxqG0zqtzSEz_jR6GxQ_KBYh2eVCZKp.html', methods=['GET'])
def authorize_zalo():
    '''
        Route này dùng để authorize domain theo yêu cầu của Zalo
    '''
    return render_template(r'zalo_verifierJ8BkCwxqG0zqtzSEz_jR6GxQ_KBYh2eVCZKp.html')

# Webhook for Facebook
@app.route('/webhook', methods=['POST'])
def fb_webhook():
    data = request.get_json()
    logger.info(data)
    user_id = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']

    if 'is_echo' in data['entry'][0]['messaging'][0] and data['entry'][0]['messaging'][0]['is_echo']:
        event_name = 'oa_send_text'
    elif 'is_echo' not in data['entry'][0]['messaging'][0]:
        event_name = 'user_send_text'
    else:
        event_name = None

    ### Only send to dev, remove in production ###
    if user_id not in ['9362337113891359']:
        logger.info("Return 200 OK")
        return 'OK', 200
    logger.info("user is dev")
    ##############################################

    if event_name:
        msg_queue.put(('fb', user_id, message, event_name))
        logger.info("Put message to queue")
    return 'OK', 200

@app.route('/webhook', methods=['GET'])
def fb_webhook_verify():
    data = request.args
    mode = data.get('hub.mode')
    challenge = data.get('hub.challenge')
    verify_token = data.get('hub.verify_token')
    logger.info(mode)
    logger.info(challenge)
    logger.info(verify_token)
    if mode == 'subscribe' and verify_token == 'tglwater':
        return challenge, 200
    return 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)

