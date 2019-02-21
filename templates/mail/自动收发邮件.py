
from flask import Flask, request

from flask_mail import Mail, Message

from threading import Thread
import os
 
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '724995297@qq.com'
app.config['MAIL_PASSWORD'] = ''
mail = Mail(app)
 
msg = Message('标题', sender='724995297@qq.com', recipients=['724995297@qq.com'])
msg.body = '内容'

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
 
@app.route('/send_email')
def send_email():
    msg.body = '内容'
    thread = Thread(target=send_async_email, args=[app, msg])
    thread.start()
    return 'success'
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port = 56789,debug=True)
