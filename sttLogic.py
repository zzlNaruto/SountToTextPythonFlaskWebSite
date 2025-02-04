# -*- coding: utf8 -*-
import os
import json
import time
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import requests
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from deleteLogic import delete_file
def file_trans(filename) :
    # 地域ID，固定值。
    REGION_ID = "cn-beijing"
    PRODUCT = "nls-filetrans"
    DOMAIN = "filetrans.cn-beijing.aliyuncs.com"
    API_VERSION = "2018-08-17"
    POST_REQUEST_ACTION = "SubmitTask"
    GET_REQUEST_ACTION = "GetTaskResult"
    # 请求参数
    KEY_APP_KEY = "appkey"
    KEY_FILE_LINK = "file_link"
    KEY_VERSION = "version"
    KEY_ENABLE_WORDS = "enable_words"
    # 是否开启智能分轨
    KEY_AUTO_SPLIT = "auto_split"
    # 响应参数
    KEY_TASK = "Task"
    KEY_TASK_ID = "TaskId"
    KEY_STATUS_TEXT = "StatusText"
    KEY_RESULT = "Result"
    KEY_SENTENCES = "Sentences"
    KEY_TEXT = "Text"
    # 状态值
    STATUS_SUCCESS = "SUCCESS"
    STATUS_RUNNING = "RUNNING"
    STATUS_QUEUEING = "QUEUEING"

    accessKeyId = os.getenv("OSS_ACCESS_KEY_ID")
    accessKeySecret = os.getenv("OSS_ACCESS_KEY_SECRET")

    # 创建AcsClient实例
    client = AcsClient(accessKeyId, accessKeySecret, REGION_ID)
    # 提交录音文件识别请求
    postRequest = CommonRequest()
    postRequest.set_domain(DOMAIN)
    postRequest.set_version(API_VERSION)
    postRequest.set_product(PRODUCT)
    postRequest.set_action_name(POST_REQUEST_ACTION)
    postRequest.set_method('POST')

    # 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
    auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
    # 填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
    endpoint = "https://oss-cn-beijing.aliyuncs.com"

    # 填写Endpoint对应的Region信息，例如cn-hangzhou。注意，v4签名下，必须填写该参数
    region = "cn-beijing"

    # yourBucketName填写存储空间名称。
    bucket_name = "standai-stt-bucket"

    bucket = oss2.Bucket(auth, endpoint, bucket_name, region=region)

    appKey = os.getenv("STT_APP_KEY")

    # 生成下载文件的签名URL，有效时间为3600秒。
    # 设置slash_safe为True，OSS不会对Object完整路径中的正斜线（/）进行转义，此时生成的签名URL可以直接使用。
    fileUrl = bucket.sign_url('GET', 'sttFile/'+filename, 3600, slash_safe=True)

    # fileUrl = "https://stt-bucket.oss-cn-beijing.aliyuncs.com/helloworld/nls-sample-16k.wav?Expires=1733845668&OSSAccessKeyId=TMP.3KfozSkfUsJXDLc784yEQ3sqTuo14kv2YmjAD6veRVmNuajA7deYLW9rvjsMdj461JnW4Rz3U1Ygvmm6iXCGy295AxMqqA&Signature=I67YF2f1NLo13RP3Or91M3b2Sm4%3D"
    # fileUrl = "https://stt-bucket.oss-cn-beijing-internal.aliyuncs.com/helloworld/nls-sample-16k.wav"

    # 新接入请使用4.0版本，已接入（默认2.0）如需维持现状，请注释掉该参数设置。
    # 设置是否输出词信息，默认为false，开启时需要设置version为4.0。
    task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileUrl, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False}
    # 开启智能分轨，如果开启智能分轨，task中设置KEY_AUTO_SPLIT为True。
    # task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, KEY_AUTO_SPLIT : True}
    task = json.dumps(task)
    print(task)
    postRequest.add_body_params(KEY_TASK, task)
    taskId = ""
    try :
        postResponse = client.do_action_with_exception(postRequest)
        postResponse = json.loads(postResponse)
        print (postResponse)
        statusText = postResponse[KEY_STATUS_TEXT]
        if statusText == STATUS_SUCCESS :
            print ("录音文件识别请求成功响应！")
            taskId = postResponse[KEY_TASK_ID]
        else :
            print ("录音文件识别请求失败！")
            return
    except ServerException as e:
        print (e)
    except ClientException as e:
        print (e)
    # 创建CommonRequest，设置任务ID。
    getRequest = CommonRequest()
    getRequest.set_domain(DOMAIN)
    getRequest.set_version(API_VERSION)
    getRequest.set_product(PRODUCT)
    getRequest.set_action_name(GET_REQUEST_ACTION)
    getRequest.set_method('GET')
    getRequest.add_query_param(KEY_TASK_ID, taskId)
    # 提交录音文件识别结果查询请求
    # 以轮询的方式进行识别结果的查询，直到服务端返回的状态描述符为"SUCCESS"、"SUCCESS_WITH_NO_VALID_FRAGMENT"，
    # 或者为错误描述，则结束轮询。
    statusText = ""
    while True :
        try :
            getResponse = client.do_action_with_exception(getRequest)
            getResponse = json.loads(getResponse)
            print (getResponse)
            statusText = getResponse[KEY_STATUS_TEXT]
            if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING :
                # 继续轮询
                time.sleep(10)
            else :
                # 退出轮询
                break
        except ServerException as e:
            print (e)
        except ClientException as e:
            print (e)
    if statusText == STATUS_SUCCESS :
        print ("录音文件识别成功！")
        contentText = getResponse[KEY_RESULT][KEY_SENTENCES][0][KEY_TEXT]
        print (contentText)
        delete_file(filename)
        return {'message': 'Success', 'payload': contentText, 'code': 'S'}
    else :
        print ("录音文件识别失败！")
        contentText = '录音文件识别失败！'
        delete_file(filename)
        return {'message': 'Error', 'payload': contentText, 'code': 'E'}

# 填写Object完整路径，例如exampledir/exampleobject.txt。Object完整路径中不能包含Bucket名称。
filename = 'helloworld/nls-sample-16k.wav'


# 执行录音文件识别
# file_trans(object_name)