from flask import Flask, request, jsonify, render_template
import threading
from src.worker import worker, msg_queue, load_config
from src.utils import *
from src.logger import logger
import traceback

# Chạy worker trong process riêng
threading.Thread(target=worker, daemon=True).start()

app = Flask(__name__)

# Webhook for Zalo
@app.route("/", methods=['POST'])
def webhook():
    '''
        Webhook endpoint của Zalo
    '''
    # Nhận user id và tin nhắn
    data = request.get_json()
    logger.info(data)
    event_name = data['event_name']
    try:
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
                msg_queue.put(('zalo', user_id, message, event_name, None))
                logger.info("Put message to queue")
            except Exception as e:
                logger.error(e)
                raise e
        elif event_name == 'oa_send_text':
            if 'admin_id' in data['sender']:
                user_id = data['recipient']['id']
                msg_queue.put(('zalo', user_id, None, event_name, None))
                logger.info("Put message to queue")
        else:
            logger.info('Event name not in [user_send_text, anonymous_send_text, oa_send_text]')
    except Exception as e:
        logger.info(traceback.format_exc())

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
    '''
        Webhook endpoint của Facebook
    '''
    try:
        data = request.get_json()
        logger.info(data)
        message = None
        mid = data['entry'][0]['messaging'][0]['message']['mid']

        if 'is_echo' in data['entry'][0]['messaging'][0]['message']:
            event_name = 'fb_echo'
            user_id = data['entry'][0]['messaging'][0]['recipient']['id']
        elif 'is_echo' not in data['entry'][0]['messaging'][0]['message']:
            event_name = 'user_send_text'
            user_id = data['entry'][0]['messaging'][0]['sender']['id']
            message = data['entry'][0]['messaging'][0]['message']['text']
        else:
            event_name = None

        logger.info(event_name)

        ### Only send to dev, remove in production ###
        # if user_id not in ['9362337113891359', '6539779106135592'] and event_name == 'user_send_text':
        #     logger.info("Return 200 OK")
        #     return 'OK', 200
        # logger.info("user is dev")
        ##############################################

        if event_name:
            msg_queue.put(('fb', user_id, message, event_name, mid))
            logger.info("Put message to queue")
    except Exception as e:
        logger.info(traceback.format_exc())
    return 'OK', 200

@app.route('/webhook', methods=['GET'])
def fb_webhook_verify():
    '''
        Method để verify theo yêu cầu của Facebook
    '''
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

@app.route('/webhook_tectonic', methods=['GET'])
def fb_webhook_verify_tectonic():
    '''
        Method để verify theo yêu cầu của Facebook dành cho Tectonic
    '''
    data = request.args
    mode = data.get('hub.mode')
    challenge = data.get('hub.challenge')
    verify_token = data.get('hub.verify_token')
    logger.info(mode)
    logger.info(challenge)
    logger.info(verify_token)
    if mode == 'subscribe' and verify_token == 'tectonic':
        return challenge, 200
    return 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)

