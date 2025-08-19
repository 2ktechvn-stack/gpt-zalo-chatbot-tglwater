import yaml
import requests
from src.logger import logger

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
        print(response.content)
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
    print(user_id, reply)
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
        print(response.status_code, response.content)
        if response.json()['error'] == -216:
            config = check_zalo_oa_token(config, refresh=True)
        else:
            break
        