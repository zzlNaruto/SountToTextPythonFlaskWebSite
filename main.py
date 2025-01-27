from flask import Flask, render_template, request, jsonify, redirect, url_for,Response
from werkzeug.utils import secure_filename
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import os,sys
import time
import threading
from sttLogic import fileTrans


# 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())

# 填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
endpoint = "https://oss-cn-beijing.aliyuncs.com"

# 填写Endpoint对应的Region信息，例如cn-hangzhou。注意，v4签名下，必须填写该参数
region = "cn-beijing"

# yourBucketName填写存储空间名称。
bucket = oss2.Bucket(auth, endpoint, "stt-bucket", region=region)

app = Flask(__name__)

# 存储上传进度的字典，避免覆盖问题
uploadProgress = {}

# 启动一个线程锁，确保线程安全
lock = threading.Lock()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploadFile', methods=['POST'])
def uploadFile():
    if 'audio_file' not in request.files:
        return "No file part", 400
    file = request.files['audio_file']
    if file.filename == '':
        return "No selected file", 400
    filename = secure_filename(file.filename)
    # 根据按钮的 value 执行不同操作
    print(request.form)  # 打印接收到的表单数据
    action = request.form.get('action')
    print('action:', action)

    if action == 'bottonSoundToText':
        print('bottonSoundToText')
        # 每个文件都拥有独立的进度信息
        with lock:
            uploadProgress[filename] = {'percentage': 0}

        def saveFileWithProgress():
            # consumed_bytes表示已上传的数据量。
            # total_bytes表示待上传的总数据量。当无法确定待上传的数据长度时，total_bytes的值为None。
            def percentage(consumed_bytes, total_bytes):
                if total_bytes:
                    rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                    # 更新文件上传进度
                    with lock:
                        uploadProgress[filename]['percentage'] = rate
                    sys.stdout.flush()
            # 使用文件对象上传到 OSS
            fileData = file.read()
            bucket.put_object('sttFile/'+filename, fileData,progress_callback=percentage)
            # 上传完成后，设置上传进度为100
            with lock:
                uploadProgress[filename]['percentage'] = 100

        # 启动后台线程进行文件上传
        threading.Thread(target=saveFileWithProgress, daemon=True).start()
        # 音频转文字在这里调用有问题，需要在网页端接收到上传完成后的状态再调用
        return jsonify({'message': 'File uploaded successfully', 'action': 'bottonSoundToText', 'code': 'S', 'filename': filename}), 200
    elif action == 'bottonRegenerate':
        # 在这里添加语音转文字的逻辑
        print('bottonRegenerate')
        returnJson = fileTrans(filename)
        convertedText = returnJson.payload
        print(convertedText)
        return returnJson, 200
    else:
        print('Invalid')
        return "Invalid action", 400

@app.route('/progress')
def progress():
    """
    通过 SSE 向前端推送上传进度
    """
    def generate():
        while True:
            with lock:
                # 只推送每个文件的上传进度
                for filename, progress_data in uploadProgress.items():
                    print('\r{0}% '.format(progress_data['percentage']), end='')
                    yield f"data: {{\"file\": \"{filename}\", \"percentage\": {progress_data['percentage']}}}\n\n"
            time.sleep(0.5)  # 每秒钟推送一次进度

    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/soundToText', methods=['POST'])
def soundToText():
    data = request.json
    print(data)
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    # 提取具体的键值
    filename = data.get('filename')

    # 返回处理后的响应
    # returnText = fileTrans(filename)
    returnText = jsonify({
                            'message': 'Success', 'payload': 'contentText', 'code': 'S'
                        })
    if returnText.code == 'S':
        # print(returnText)
        return returnText, 200
    elif returnText.code == 'E':
        return returnText, 400
