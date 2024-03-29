import json
import os

from flask import Flask,render_template, request, jsonify

from db_utils import read_csv_and_write_to_database, employee_engine, customer_financial_engine, generate_image, \
    encode_image

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('chart.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']

    # 假设这里是您的对话逻辑，生成了文本回复和图片回复
    bot_text_response = "GPT：" + user_message  # 示例文本回复
    # 示例图片回复
    image_data = generate_image()  # 生成图片数据的函数
    image_response = encode_image(image_data)  # 将图片数据编码为Base64字符串

    # 检查请求头中的 Accept 字段，以确定客户端期望的数据类型
    accept_header = request.headers.get('Accept')
    if (accept_header and 'image' in accept_header) or "图片" in user_message:
        # 如果客户端期望接收图片数据，则返回图片
        return jsonify({'image': image_response})
    else:
        # 否则返回文本数据
        return jsonify({'message': bot_text_response})

# 上传文件的视图函数
@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'})

    files = request.files.getlist('files')

    if not files:
        return jsonify({'error': 'No files selected'})

    file_paths = []
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'One or more files have empty names'})
        else:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            file_paths.append(file_path)

    # 调用函数将数据写入不同的数据库
    for file_path in file_paths:
        if '员工信息' in file_path.lower():
            read_csv_and_write_to_database(file_path, employee_engine,"EmployeeInformation")
        elif '客户信息' in file_path.lower():
            read_csv_and_write_to_database(file_path, customer_financial_engine,"CustomerInformation")
        elif '财务信息' in file_path.lower():
            read_csv_and_write_to_database(file_path, customer_financial_engine,"FinancialInformation")

    return jsonify({'success': 'Write to database successful',"filename":file_paths})






if __name__ == '__main__':
    app.run(debug=True)
