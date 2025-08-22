from flask import Flask, request, jsonify, render_template
import threading
from src.worker import worker, msg_queue, load_config
from src.utils import *
from src.logger import logger

# Chạy worker trong process riêng
threading.Thread(target=worker, daemon=True).start()

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def webhook():
    # Nhận user id và tin nhắn
    data = request.get_json()
    logger.info(data)
    event_name = data['event_name']

    if event_name in ['user_send_text', 'anonymous_send_text']:
        try:
            user_id = data['sender']['id']

            ### Only send to dev, remove in production ###
            if user_id not in ['8174221521790538039', '2656106822398634139']:
                logger.info("Return 200 OK")
                return 'OK', 200
            logger.info("user is dev")
            ##############################################
            
            message = data['message']['text']

            # Đem vào hàng chờ để đảm bảo thời gian phản hồi theo yêu cầu của Zalo
            msg_queue.put((user_id, message))
            logger.info("Put message to queue")
        except Exception as e:
            logger.error(e)
            raise e
    else:
        logger.info('Event name not in [user_send_text, anonymous_send_text]')

    logger.info("Return 200 OK")
    return 'OK', 200

@app.route('/zalo_verifierJ8BkCwxqG0zqtzSEz_jR6GxQ_KBYh2eVCZKp.html', methods=['GET'])
def authorize_zalo():
    '''
        Route này dùng để authorize domain theo yêu cầu của Zalo
    '''
    return render_template(r'zalo_verifierJ8BkCwxqG0zqtzSEz_jR6GxQ_KBYh2eVCZKp.html')

if __name__ == '__main__':
    app.run(ssl_context=("cert.pem", "key.pem"), debug=True, use_reloader=True)
