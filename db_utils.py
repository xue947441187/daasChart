import base64
from io import BytesIO

import pandas as pd
from sqlalchemy import create_engine
from PIL import Image, ImageDraw

employee_db_uri = 'mysql://root:123456@localhost/employee_db'
employee_engine = create_engine(employee_db_uri)

# 配置存储客户信息以及财务信息的数据库连接
customer_financial_db_uri = 'mysql://root:123456@localhost/customer_financial_db'
customer_financial_engine = create_engine(customer_financial_db_uri)

# 读取CSV并写入数据库的函数
def read_csv_and_write_to_database(file_path, engine,table_name):
    # 使用Pandas读取数据
    df = pd.read_csv(file_path,encoding='GBK')  # 如果上传的是CSV文件，如果是其他格式的文件，请相应修改
    # 将数据写入数据库
    df.to_sql(table_name, engine, if_exists='append', index=False)  # 将数据写入数据库，如果表不存在则自动创建


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

