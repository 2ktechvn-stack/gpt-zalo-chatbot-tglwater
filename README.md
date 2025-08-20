# gpt-zalo-chatbot-tglwater
Chatbot GPT kết nối Zalo OA cho TGLWater

To-do list:
- Webhook nhận tin Zalo (Not yet)
- Gửi tin sang GPT
- Nhận phản hồi và gửi lại Zalo OA
- Triển khai lên domain của anh, test online

What am I doing until now:
- Tạo "ứng dụng" tại Zalo Developers: https://developers.zalo.me/app/4308894772848703225/
- Lấy Access Token và Refresh Token
- Giả lập ChatGPT dùng Ollama server
- Tạo server cho webhook
- Tạo queue để xử lý tin nhắn chờ

Next task:
- Gắn ChatGPT
- Làm function lưu thông tin người dùng
- cấu hình dns

Requirements:
- Python 3.10.11
- python3.10 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app
- Copy chatbot.service to /etc/systemd/system

Exit checklist:
- Gửi riêng file config.yaml
- Transfer app trên Zalo cho owner (thêm owner làm amin, đổi sdt và email, exit)
- Merge dev -> main
- Exit github

References:
- https://developers.zalo.me/docs/official-account/webhook/quan-ly/su-kien-nguoi-dung-dong-y-chia-se-thong-tin (Có thể lấy SDT user khi họ đã ấn follow)
- https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04
- https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-22-04#step-4-configuring-uwsgi