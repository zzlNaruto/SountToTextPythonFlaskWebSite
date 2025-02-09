from flask import Flask, render_template, request, jsonify, redirect, url_for,Response
from werkzeug.utils import secure_filename
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import os,sys
import time
import threading
from sttLogic import file_trans
from flask_socketio import SocketIO, emit


# 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())

# 填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
endpoint = "https://oss-cn-beijing.aliyuncs.com"

# 填写Endpoint对应的Region信息，例如cn-hangzhou。注意，v4签名下，必须填写该参数
region = "cn-beijing"

# yourBucketName填写存储空间名称。
bucket = oss2.Bucket(auth, endpoint, "standai-stt-bucket", region=region)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储上传进度的字典，避免覆盖问题，使用websocket传输进度就不需要了，而且用fetch上传文件时，无法通过轮询获取当前上传进度
# uploadProgress = {}

# 启动一个线程锁，确保线程安全
# lock = threading.Lock()

MAX_FILE_SIZE = {
    "Audio": 500 * 1024 * 1024,  # 500MB
    "Video": 2000 * 1024 * 1024  # 2000MB
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check-filesize', methods=['POST'])
def check_filesize():
    if 'audio_file' not in request.files:
        return "No file part", 400
    file = request.files['audio_file']
    if file.filename == '':
        return "No selected file", 400
    filename = secure_filename(file.filename)

    file_type = "Audio" if file.mimetype.startswith("audio") else "Video"

    print(file_type)

    # 获取文件大小
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小（字节）
    file.seek(0)  # 重新回到文件开头，防止影响后续处理

    # 检查文件大小是否超过限制
    if file_size > MAX_FILE_SIZE[file_type]:
        payload = f"{file_type} File size is too large. {file_type} file maximum support {MAX_FILE_SIZE[file_type] / (1024 * 1024)}MB"
        print(payload)
        return jsonify({'message': 'File size is too large', 'payload': payload, 'code': 'E'}), 400
    else:
        return jsonify({'message': '', 'payload': payload, 'code': 'S'}), 200
    
@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'audio_file' not in request.files:
        return "No file part", 400
    file = request.files['audio_file']
    if file.filename == '':
        return "No selected file", 400
    filename = secure_filename(file.filename)
    print('filename from /upload-file secure_filename:',filename)
                                                          
    # 根据按钮的 value 执行不同操作
    print(request.form)  # 打印接收到的表单数据
    action = request.form.get('action')
    print('action from /upload-file:', action)

    if action == 'botton_sound_to_text':
        print('botton_sound_to_text')
        # 每个文件都拥有独立的进度信息
        # with lock:
        # uploadProgress[filename] = {'percentage': 0}

        # def saveFileWithProgress():
        # consumed_bytes表示已上传的数据量。
        # total_bytes表示待上传的总数据量。当无法确定待上传的数据长度时，total_bytes的值为None。
        last_emit_time = time.time()
        def percentage(consumed_bytes, total_bytes):
            nonlocal last_emit_time
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                # 更新文件上传进度
                # with lock:
                # uploadProgress[filename]['percentage'] = rate
                current_time = time.time()
                # 2秒更新一次进度
                if current_time - last_emit_time > 2.0:
                    print('uploadProgress from /upload-file/percentage:',rate)  # 每隔2S打印接收到的表单数据
                    socketio.emit('upload-progress', {'filename': filename, 'percentage': rate})  # 直接推送进度
                    socketio.sleep(0)
                    last_emit_time = current_time  # 更新上次发送
        # 使用文件对象上传到 OSS
        fileData = file.read()
        bucket.put_object('sttFile/'+filename, fileData,progress_callback=percentage)
        # 上传完成后，设置上传进度为100
        # with lock:
        # uploadProgress[filename]['percentage'] = 100
        socketio.emit('upload-progress', {'file': filename, 'percentage': 100})  # 直接推送进度

        # 启动后台线程进行文件上传
        # threading.Thread(target=saveFileWithProgress, daemon=True).start()
        # 音频转文字在这里调用有问题，需要在网页端接收到上传完成后的状态再调用
        return jsonify({'message': '文件上传成功', 'action': 'botton_sound_to_text', 'code': 'S', 'filename': filename}), 200
    elif action == 'botton_regenerate':
        # 在这里添加语音转文字的逻辑
        print('botton_regenerate')
        return_json = file_trans(filename)
        converted_text = return_json.payload
        print('converted_text from /upload-file:', converted_text)
        return return_json, 200
    else:
        print('Invalid')
        return "Invalid action", 400

# @app.route('/progress')
# def progress():
    """
    通过 SSE 向前端推送上传进度
    """
    # def generate():
        # while True:
            # with lock:
            #     # 只推送每个文件的上传进度
            #     for filename, progress_data in uploadProgress.items():
            #         print('\r{0}% '.format(progress_data['percentage']), end='')
            #         yield f"data: {{\"file\": \"{filename}\", \"percentage\": {progress_data['percentage']}}}\n\n"
            # time.sleep(0.5)  # 每秒钟推送一次进度

    # return Response(generate(), content_type='text/event-stream')

# @app.route('/upload-progress', methods=['GET'])
# def upload_progress():
    # with lock:
    # filename = request.args.get('filename')
    # print('filename from /upload-progress:',filename)  # 打印接收到的表单数据
    # print('uploadProgress from /upload-progress:',uploadProgress)  # 打印接收到的表单数据
    # progress = uploadProgress.get(filename)
    # if not progress:
    #     progress = {'percentage': -1}
    # return jsonify(progress)

@app.route('/sound-to-text', methods=['POST'])
def sound_to_text():
    data = request.json
    print(data)
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    # 提取具体的键值
    filename = data['filename']
    if not filename:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    # 返回处理后的响应
    return_json = file_trans(filename)
    print(return_json)
    message = return_json.get('message')  # 获取 "message" 字段
    payload = return_json.get('payload')  # 获取 "payload" 字段
    code = return_json.get('code')  # 获取 "code" 字段
    if return_json['code'] == 'S':  # 确保返回成功
        # 根据获取的内容返回适当的响应
        return jsonify({'message': message, 'payload': payload, 'code': code}), 200

    else:
        return jsonify({'message': message, 'payload': payload, 'code': code}), 400
    
@socketio.on('connect')
def handle_connect():
    print("客户端已连接")

@socketio.on('disconnect')
def handle_disconnect():
    print("客户端已断开连接")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

