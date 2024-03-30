import base64
import re
from io import BytesIO

import pandas as pd
from matplotlib import pyplot as plt
from sqlalchemy import create_engine, text
from PIL import Image, ImageDraw

employee_db_uri = 'postgresql://employee:Employee123*@SG-employee-db-5251-pgsql-master.servers.mongodirector.com:5432/employee_db'
employee_engine = create_engine(employee_db_uri)

# 配置存储客户信息以及财务信息的数据库连接
customer_financial_db_uri = 'mysql://cfinancial:Cfinancial123*@SG-customer-financial-db-8291-mysql-master.servers.mongodirector.com:3306/customer_financial_db'
customer_financial_engine = create_engine(customer_financial_db_uri)

# 读取CSV并写入数据库的函数
def read_csv_and_write_to_database(file_path, engine,table_name):
    # 使用Pandas读取数据
    df = pd.read_csv(file_path,encoding='GBK')  # 如果上传的是CSV文件，如果是其他格式的文件，请相应修改
    df.reset_index(inplace=True)
    df.rename(columns={
        "index":"id"
    },inplace=True)
    df["id"] = df["id"] + 1
    # 将数据写入数据库
    df.to_sql(table_name, engine, if_exists='append', index=False)  # 将数据写入数据库，如果表不存在则自动创建
    # 设置主键约束
    with engine.connect() as connection:
        if table_name == 'EmployeeInformation':
            sql_statement  = text("""
                 ALTER TABLE public."EmployeeInformation"
                ADD CONSTRAINT unique_id UNIQUE (id),
                ADD CONSTRAINT id PRIMARY KEY (id);


            """)
        else:
            # 假设你想将 'Name' 字段作为主键
            sql_statement = text(f"""ALTER TABLE {table_name}
                        CHANGE COLUMN `id` `id` BIGINT NOT NULL ,
                        ADD PRIMARY KEY (`id`);
                        ;
                """)
        try:
            connection.execute(sql_statement)
            connection.commit()
        except Exception as e:
            print(e)


def generate_image():
    # 示例函数：生成图片数据
    # 您可以在这里使用任何生成图片的逻辑，比如使用PIL库、matplotlib等
    # 这里简单地返回一个示例图片数据（白色背景上的黑色文本）

    img = Image.new('RGB', (200, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Sample nihao", fill=(0, 0, 0))

    return img


def encode_image(image):
    # 将图片数据编码为Base64字符串
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# def get_chart_type(input_type):
#     chart_types = {
#         '柱状图': 'bar',
#         '折线图': 'line',
#         '散点图': 'scatter',
#         '箱线图': 'box',
#         # 可根据需要添加其他类型
#     }
#
#     # 如果用户输入的类型在备选类型中，则返回相应的图表类型；否则返回用户输入的类型的小写形式
#     return chart_types.get(input_type.lower(), input_type.lower())
#

def get_chart_type(input_text):
    # 定义正则表达式模式，用于匹配不同类型的图表名称
    patterns = {
        '柱状图': r'(柱状图|bar)',
        '折线图': r'(折线图|line)',
        '散点图': r'(散点图|scatter)',
        '箱线图': r'(箱线图|box)'
        # 可根据需要添加其他类型的图表名称和对应的正则表达式
    }

    # 遍历图表类型和正则表达式模式，查找匹配的图表类型
    for chart_type, pattern in patterns.items():
        if re.search(pattern, input_text, re.IGNORECASE):
            chart_types = {
                '柱状图': 'bar',
                '折线图': 'line',
                '散点图': 'scatter',
                '箱线图': 'box',
                # 可根据需要添加其他类型
            }

            return chart_types.get(chart_type.lower(), chart_type.lower())

    # 如果没有匹配的图表类型，则返回 None
    return None


def plot_chart_from_db(engine,query, chart_type="line"):
    if chart_type == None:
        return  None
    # 从数据库中读取数据
    df = pd.read_sql_query(query, engine)

    # 将 Date 列转换为日期时间类型
    df['Date'] = pd.to_datetime(df['Date'])

    # 绘制图形
    plt.figure(figsize=(10, 6))

    if chart_type == 'bar':
        # 绘制柱状图
        plt.bar(df['Date'], df['Total_Sales'], color='skyblue')
    elif chart_type == 'line':
        # 绘制折线图
        plt.plot(df['Date'], df['Total_Sales'], marker='o', color='green', linestyle='-')
    elif chart_type == 'scatter':
        # 绘制散点图
        plt.scatter(df['Date'], df['Total_Sales'], color='red')
    elif chart_type == 'box':
        # 绘制箱线图
        plt.boxplot(df['Total_Sales'])

    plt.title('Total Sales Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Sales')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 将图形保存到内存中
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    # 清空图形以避免重复绘制
    plt.clf()

    # 获取图片数据的字节对象
    image_data = buffer.getvalue()

    # 将图片数据编码为 Base64 字符串
    encoded_image = base64.b64encode(image_data).decode('utf-8')

    return encoded_image


# 示例查询
# query = "SELECT * FROM FinancialInformation;"

# 调用函数并绘制柱状图
# plot_bar_chart_from_db(customer_financial_engine, query)


def modify_query_with_year(input_text):
    # 定义正则表达式模式，用于匹配时间信息
    pattern = r'(\d{2,4})年?'

    # 查找匹配的时间信息
    match = re.search(pattern, input_text)
    if match:
        # 提取匹配到的年份
        year = match.group(1)

        # 根据年份的长度调整格式
        if len(year) == 2:
            year = f'20{year}'  # 两位数年份转换成四位数形式

        # 构建查询语句，将查询年份替换为匹配到的年份
        modified_query = f"SELECT * FROM FinancialInformation WHERE YEAR(Date) = {year};"
        return modified_query
    else:
        # 如果未找到匹配的时间信息，则直接返回原始查询语句
        return "SELECT * FROM FinancialInformation WHERE YEAR(Date) = 2023;"


def parse_user_message(user_message):
    # 定义正则表达式模式，用于匹配年份信息、柱状图关键词和姓名
    year_pattern = r'(\d{2,4})年?'
    # bar_chart_keywords = r'(柱状图|bar)'
    name_pattern = r'(?:帮我查询一下)?([^\s,]+)的信息'
    chart_keywords = r'(柱状图|bar|折线图|line|散点图|scatter|饼图|pie)'

    # 查找匹配的年份信息、柱状图关键词和姓名
    has_year = re.search(year_pattern, user_message) is not None
    has_bar_chart_keyword = re.search(chart_keywords, user_message, re.IGNORECASE) is not None
    match = re.search(name_pattern, user_message)
    name = match.group(1) if match else None

    return has_year, has_bar_chart_keyword, name



# 示例输入
# input_text = "展示23年数据"

def execute_query_to_get_result(query):
    try:
        # 使用 Pandas 的 read_sql_query 函数执行查询并获取结果
        result = pd.read_sql_query(query, employee_engine)
        return result
    except Exception as e:
        print("Error:", e)
        return None
def parse_modify_phone_message(user_message):
    # 定义正则表达式模式，用于匹配姓名和新的手机号
    pattern = r'修改([^的]+)的手机号\S*?(\d+)'


    # 查找匹配的姓名和新的手机号
    match = re.search(pattern, user_message)
    if match:
        # 提取匹配到的姓名和新的手机号
        name = match.group(1).strip()
        new_phone = match.group(2).strip()
        return name, new_phone
    else:
        # 如果未找到匹配的信息，则返回空
        return None, None



def update_phone_number_in_database(name, new_phone):
    # 构建 SQL 更新语句
    try:
        select_query = text(f"""SELECT id, "name", age, height, weight, department, phone
            FROM public."EmployeeInformation" WHERE "name" = '{name}';""")

        df = execute_query_to_get_result(select_query)
        # 查询 index 主键
        with employee_engine.connect() as connection:
            query = text(f"""
            UPDATE public."EmployeeInformation" SET phone = {int(new_phone)} WHERE "id" = {df["id"][0]};""")
            connection.execute(query)
            print("电话号码更新成功")
            connection.commit()
            # result = connection.execute(select_query)
            # index_row = result.fetchone()
            # if index_row:
            #     index = index_row[0]
                # 构建 SQL 更新语句

                # 执行 SQL 更新语句
    except Exception as e:
        print("电话号码更新失败:", e)
        return False

    return True
