# 使用 Python 作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /myWorkDIr

# 复制项目文件到容器中
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露应用运行的端口
EXPOSE 5000

# 使用 Gunicorn 启动 Flask 应用
CMD ["gunicorn", "-w", "4", "main:app", "--host=0.0.0.0", "--port=5000"]