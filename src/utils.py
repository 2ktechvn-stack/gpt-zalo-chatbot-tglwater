import yaml
import requests
from src.logger import logger
import sqlite3
from datetime import datetime

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
        logger.error(e)
        raise e

def save_config(config):
    # Write YAML file
    logger.info('Saving config')
    try:
        with open('config.yaml', 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)
        logger.info("Saved successfully!")
    except Exception as e:
        logger.error(e)
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
        logger.error(e)
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
        
def init_db():
    """Initialize the database and create table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            time_created TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_thread(thread_id: str, user_id: str):
    """Insert a new thread into the database with current timestamp."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO threads (thread_id, user_id, time_created)
        VALUES (?, ?, ?)
    """, (thread_id, user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_threads(user_id: str = None):
    """Retrieve all threads, or only those belonging to a specific user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT thread_id, user_id, time_created FROM threads WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT thread_id, user_id, time_created FROM threads")
    rows = cursor.fetchall()
    conn.close()
    return rows