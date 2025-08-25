# gpt-zalo-chatbot-tglwater
Chatbot GPT kết nối Zalo OA cho TGLWater

To-do list:
- Webhook nhận tin Zalo (Not yet)
- Gửi tin sang GPT
- Nhận phản hồi và gửi lại Zalo OA
- Triển khai lên vps, cấu hình domain, test online

Prequisite:
- Ubuntu 22.04
- Python 3.10.x

Installation:
- ufw enable
- apt update
- apt install nginx
- ufw allow 'Nginx HTTP'
- ufw status
- mkdir /app
- cd /app
- git clone https://github.com/2ktechvn-stack/gpt-zalo-chatbot-tglwater.git
- cd gpt-zalo-chatbot-tglwater
- <Copy config.yaml file to this folder>
- pip install -r requirements.txt
- cp chatbot.service to /etc/systemd/system
- chgrp www-data /app
- systemctl start chatbot (run server in background)
- systemctl enable chatbot (enable server run on startup)
- cp chatbot /etc/nginx/sites-available/
- ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled
- unlink /etc/nginx/sites-enabled/default
- nginx -t
- systemctl restart nginx
- ufw allow 'Nginx Full'
- apt install certbot python3-certbot-nginx
- certbot --nginx -d api.tglwater.com
- ufw delete allow 'Nginx HTTP'

Exit checklist:
- Gửi riêng file config.yaml
- Transfer app trên Zalo cho owner (thêm owner làm admin, đổi sdt và email, exit)
- Merge dev -> main
- tài khoản VPS: https://id.thuevpsgiare.vn/login
- cách ssh vào vps
- cách chỉnh sửa assistant (cách model nói chuyện, knowledge, lưu ý về file)
- Exit github, openai, zalo dev, zalo group

References:
- https://developers.zalo.me/docs/official-account/webhook/quan-ly/su-kien-nguoi-dung-dong-y-chia-se-thong-tin (Có thể lấy SDT user khi họ đã ấn follow