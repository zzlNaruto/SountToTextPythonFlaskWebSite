# -*- coding: utf-8 -*-
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

def delete_file(filename) :
    # 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
    auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())

    # 填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
    endpoint = "https://oss-cn-beijing.aliyuncs.com"

    # 填写Endpoint对应的Region信息，例如cn-hangzhou。注意，v4签名下，必须填写该参数
    region = "cn-beijing"

    # yourBucketName填写存储空间名称。
    bucket_name = "standai-stt-bucket"
    # examplebucket填写存储空间名称。
    bucket = oss2.Bucket(auth, endpoint, bucket_name, region=region)

    # 删除文件。
    # yourObjectName填写待删除文件的完整路径，完整路径中不包含Bucket名称，例如exampledir/exampleobject.txt。
    # 如需删除文件夹，请将yourObjectName设置为对应的文件夹名称。如果文件夹非空，则需要将文件夹下的所有文件删除后才能删除该文件夹。
    bucket.delete_object('sttFile/'+filename) 