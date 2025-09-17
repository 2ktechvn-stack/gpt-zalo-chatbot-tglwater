import yaml
import requests
from src.logger import logger
import sqlite3
from datetime import datetime, timedelta
import re
import traceback

DB_FILE = "threads.db"

def load_config():
    # Load YAML file
    logger.info("Loading config")
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        logger.info("Loaded successfully!")
        return config
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def load_remind_script():
    # Load YAML file
    logger.info("Loading remind script")
    try:
        with open("remind_script.yaml", "r") as f:
            remind_script = yaml.safe_load(f)
        logger.info("Loaded successfully!")
        return remind_script
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def save_config(config):
    # Write YAML file
    logger.info('Saving config')
    try:
        with open('config.yaml', 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)
        logger.info("Saved successfully!")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def get_zalo_oa_token(config):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'secret_key': config['ZALO_APP_KEY'],
    }

    data = {
        'refresh_token': config['ZALO_OA_REFRESH_TOKEN'],
        'app_id': config['ZALO_APP_ID'],
        'grant_type': 'refresh_token',
    }
    
    try:
        response = requests.post('https://oauth.zaloapp.com/v4/oa/access_token', headers=headers, data=data)
        logger.info(response.content)
        return response.json()
    except Exception as e:
        logger.error(traceback.format_exc())
        raise e

def check_zalo_oa_token(config, refresh=True):
    '''
        Check if Token alive else refresh
        Reference: https://stc-developers.zdn.vn/docs/v2/official-account/bat-dau/xac-thuc-va-uy-quyen-cho-ung-dung-new#d%C3%B9ng-refresh-token-%C4%91%E1%BB%83-l%E1%BA%A5y-access-token
    '''
    if not refresh:
        return config

    token = get_zalo_oa_token(config)
    config['ZALO_OA_ACCESS_TOKEN'] = token['access_token']
    config['ZALO_OA_REFRESH_TOKEN'] = token['refresh_token']

    save_config(config)

    return config


def send_message_to_zalo(user_id, reply, config):
    '''
        Send message to user via Zalo OA
        Reference: https://developers.zalo.me/docs/official-account/tin-nhan/tin-tu-van/gui-tin-tu-van-dang-van-ban
    '''
    logger.info("Send reply to " + user_id)
    while True:
        response = requests.post(
            'https://openapi.zalo.me/v3.0/oa/message/cs', 
            headers={
                'Content-Type': 'application/json',
                'access_token': config['ZALO_OA_ACCESS_TOKEN'],
            }, 
            json={
                'recipient': {
                    'user_id': user_id,
                },
                'message': {
                    'text': reply,
                },
            }
        )
        logger.info(response.status_code)
        logger.info(response.content)
        if response.json()['error'] == -216:
            config = check_zalo_oa_token(config, refresh=True)
        else:
            break

def send_message_to_fb(user_id, reply, config):
    logger.info("Send reply to " + user_id)
    
    headers = {
        'Content-Type': 'application/json',
    }

    params = {
        'access_token': config['FACEBOOK_TOKEN'],
    }

    json_data = {
        'recipient': {
            'id': user_id,
        },
        'messaging_type': 'RESPONSE',
        'message': {
            'text': reply,
        },
    }

    response = requests.post(
        f'https://graph.facebook.com/v23.0/{config["FACEBOOK_PAGE_ID"]}/messages',
        params=params,
        headers=headers,
        json=json_data,
    )
    logger.info(response.status_code)
    logger.info(response.content)

    return response.json()['message_id']

def init_db():
    """Initialize the database and create table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            user_id TEXT NOT NULL,
            time_created TEXT NOT NULL,
            recent_reply_message_id TEXT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_phone_number (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phone_number TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_last_interaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            time TEXT NOT NULL,
            count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_customer_last_interaction(user_id: str, platform: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customer_last_interaction (user_id, platform, time, count)
        VALUES (?, ?, ?, ?)
    """, (user_id, platform, datetime.now().isoformat(), 0))
    conn.commit()
    conn.close()

def update_customer_last_interaction(user_id: str, platform: str, count: int = 0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if count == 0:
        cursor.execute("""
            UPDATE customer_last_interaction
            SET time = ?, count = 0
            WHERE user_id = ? AND platform = ?
        """, (datetime.now().isoformat(), user_id, platform))
    else:
        cursor.execute("""
            UPDATE customer_last_interaction
            SET count = ?
            WHERE user_id = ? AND platform = ?
        """, (count, user_id, platform))
    conn.commit()
    conn.close()

def get_customer_last_interaction(user_id: str, platform: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, platform, time, count FROM customer_last_interaction WHERE user_id = ? AND platform = ?", (user_id, platform))
    conn.commit()
    row = cursor.fetchone()
    conn.close()
    return row

def get_all_customer_last_interaction():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, platform, time, count FROM customer_last_interaction")
    conn.commit()
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_customer_last_interaction(user_id: str, platform: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM customer_last_interaction
        WHERE user_id = ? AND platform = ?
    """, (user_id, platform))
    conn.commit()
    conn.close()

def get_user_phone_numbers():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, phone_number FROM user_phone_number")
    conn.commit()
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_user_phone_number(user_id: str, phone_number: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_phone_number (user_id, phone_number)
        VALUES (?, ?)
    """, (user_id, phone_number))
    conn.commit()
    conn.close()

def remove_user_phone_number(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM user_phone_number
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def save_employee(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (user_id)
        VALUES (?)
    """, (user_id,))
    conn.commit()
    conn.close()

def remove_employee(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM employees
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM employees")
    conn.commit()
    rows = cursor.fetchall()
    conn.close()
    return rows

# Update time_created in threads table
def update_time_created(platform: str, user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE threads SET time_created = ? WHERE user_id = ? AND platform = ?", (datetime.now().isoformat(), user_id, platform))
    conn.commit()
    conn.close()

def update_recent_reply_message_id(platform: str, user_id: str, recent_reply_message_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE threads SET recent_reply_message_id = ? WHERE user_id = ? AND platform = ?", (recent_reply_message_id, user_id, platform))
    conn.commit()
    conn.close()

def get_recent_reply_message_id(platform: str, user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT recent_reply_message_id FROM threads WHERE user_id = ? AND platform = ?", (user_id, platform))
    conn.commit()
    row = cursor.fetchone()
    conn.close()
    return row[0]

def save_thread(platform: str, thread_id: str, user_id: str):
    """Insert a new thread into the database with current timestamp."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Subtract time_created for 30 minutes
    cursor.execute("""
        INSERT INTO threads (platform, thread_id, user_id, time_created)
        VALUES (?, ?, ?, ?)
    """, (platform, thread_id, user_id, (datetime.now() - timedelta(minutes=30)).isoformat()))
    conn.commit()
    conn.close()

def get_threads(user_id: str = None, platform: str = None):
    """Retrieve all threads, or only those belonging to a specific user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if user_id and platform:
        cursor.execute("SELECT thread_id, user_id, time_created, platform FROM threads WHERE user_id = ? AND platform = ?", (user_id, platform))
    else:
        cursor.execute("SELECT thread_id, user_id, time_created, platform FROM threads")
    conn.commit()
    rows = cursor.fetchall()
    conn.close()
    return rows

def check_if_user_send_phone_number(platform: str, message: str, user_id: str, config: dict):
    phone_regex = re.compile(r"(?:\+84|(?:\+?840)|0)(3|5|7|8|9)(?:[\s\.\-]?\d){8}")
    match = phone_regex.search(message)
    if match:
        # Send message to employee
        employees = get_employees()
        for employee in employees:
            reply = f"Sdt của khách cần tư vấn ({platform}): " + match.group()
            send_message_to_zalo(employee[0], reply, config)
        reply = "Cảm ơn bạn đã gửi số điện thoại, chúng tôi sẽ liên hệ với bạn sớm nhất"
        if platform == 'zalo':
            send_message_to_zalo(user_id, reply, config)
        elif platform == 'fb':
            send_message_to_fb(user_id, reply, config)
        save_user_phone_number(user_id, match.group())
        return True
    return False
    
def check_if_user_send_admin_command(platform: str, message: str, user_id: str, config: dict):
    try:
        if message[0] == '#':
            commands = message.split(' ')
            if commands[0] == '#help':
                reply = "Bot hỗ trợ các lệnh sau:\n"
                reply += "#help: Hiển thị thông tin về các lệnh hỗ trợ\n"
                reply += "#nhanthongbaosdt: Nhận thông báo khi có khách để lại sdt (Zalo only)\n"
                reply += "#huythongbaosdt: Huỷ nhận thông báo sdt (Zalo only)\n"
                reply += "#laytatcasdt: Lấy tất cả số điện thoại khách đã gửi\n"
                reply += "#stop_chat_when_interrupt_in <minutes>: Tắt chat khi nhân viên vào nhắn tin trong <minutes> phút\n"
            elif commands[0] == '#nhanthongbaosdt' and platform == 'zalo':
                save_employee(user_id)
                reply = "Đã bật nhận thông báo sdt"
            elif commands[0] == '#huythongbaosdt' and platform == 'zalo':
                remove_employee(user_id)
                reply = "Đã huỷ nhận thông báo sdt"
            elif commands[0] == '#laytatcasdt':
                phone_numbers = get_user_phone_numbers()
                reply = "Danh sách tất cả số điện thoại khách đã gửi:\n"
                for phone_number in phone_numbers:
                    reply += phone_number[1] + "\n"
            elif commands[0] == '#stop_chat_when_interrupt_in':
                if len(commands) != 2:
                    reply = "Lệnh không hợp lệ, gõ #help để xem các lệnh"
                    return True
                try:
                    minutes = int(commands[1])
                    config['STOP_CHAT_WHEN_INTERRUPT_IN'] = minutes
                    save_config(config)
                    reply = f"Đã tắt chat khi nhân viên vào nhắn tin trong {minutes} phút"
                except ValueError:
                    reply = "Lệnh không hợp lệ, gõ #help để xem các lệnh"
            else:
                reply = "Lệnh không hợp lệ, gõ #help để xem các lệnh"
                
            if platform == 'zalo':
                send_message_to_zalo(user_id, reply, config)
            elif platform == 'fb':
                send_message_to_fb(user_id, reply, config)
            return True
    except Exception as e:
        reply = traceback.format_exc()
        logger.error(reply)
        return False