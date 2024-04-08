import json
import os

from flask import Flask,render_template, request, jsonify
from sqlalchemy import text

from db_utils import read_csv_and_write_to_database, employee_engine, customer_financial_engine, generate_image, \
    encode_image, plot_chart_from_db, get_chart_type, modify_query_with_year, parse_user_message, \
    execute_query_to_get_result, update_phone_number_in_database, parse_modify_phone_message

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/chart')
def chart():
    return render_template('chart.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data['message']

    # 假设这里是您的对话逻辑，生成了文本回复和图片回复
    bot_text_response = "GPT：" + user_message  # 示例文本回复
    has_year, has_bar_chart_keyword, has_avg_age_query, has_name = parse_user_message(user_message)

    if has_name:
        # 如果消息中包含姓名，进行数据库查询
        query = text(f"""SELECT id, "name", age, height, weight, department, phone
        FROM public."EmployeeInformation" where "name" ='{has_name}';""")
        result = execute_query_to_get_result(query)

        if not result.empty:
            # 如果查询结果不为空，展示结果给用户
            row = result.iloc[0]
            row_str = "\n".join([f"{key + ':':<10}{value}\n" for key, value in row.items()])

            return jsonify({'message': row_str})
        else:
            # 如果查询结果为空，提示用户未找到相关信息
            return jsonify({'message': '未找到相关信息'})

    elif has_avg_age_query:
        # 如果消息中包含查询员工平均年龄的要求，执行相应的操作
        query = text("""SELECT AVG(age) AS average_age FROM public."EmployeeInformation";""")
        result = execute_query_to_get_result(query)

        if not result.empty:
            # 如果查询结果不为空，获取平均年龄并返回给用户
            average_age = result.iloc[0]['average_age']
            return jsonify({'message': f'员工的平均年龄为：{average_age}'})
        else:
            # 如果查询结果为空，提示用户未找到相关信息
            return jsonify({'message': '未找到相关信息'})

    elif has_year and has_bar_chart_keyword:
        # 如果消息中包含年份和柱状图关键词，返回图片
        query = modify_query_with_year(user_message)
        image_response = plot_chart_from_db(customer_financial_engine, query, chart_type=get_chart_type(user_message))

        # 返回图片数据
        if image_response is not None:
            return jsonify({'image': image_response})

    elif '修改' in user_message and '手机号' in user_message:
        # 如果用户要修改手机号
        name, new_phone = parse_modify_phone_message(user_message)
        if name and new_phone:
            # 执行更新操作
            update_phone_number_in_database(name, new_phone)
            return jsonify({'message': f'{name}的手机号已更新为：{new_phone}'})
        else:
            return jsonify({'message': '未识别到姓名和新的手机号，请重新输入'})
    else:
        # 返回文本数据
        return jsonify({'message': bot_text_response})

    # 如果未返回图片、文本或处理姓名，暂时不处理其他情况
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
