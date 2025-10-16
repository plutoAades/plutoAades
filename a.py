import json
import mysql.connector
from datetime import datetime

# 读取 JSON 文件
with open('cleaned_dangdang_goods.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 连接数据库
conn = mysql.connector.connect(
    host='8.216.32.82',      # 数据库主机
    user='root',           # 用户名
    password='cs201219.',   # 密码
    database='shopping_mall'  # 数据库名称
)

cursor = conn.cursor()

# 逐个插入商品数据
for item in data:
    product_id = item["id"]
    name = item["name"]
    description = item["description"]
    price = item["price"]
    category = item["category"]
    created_at = item["created_at"]
    stock = item["stock"]

    try:
        # 插入 products_product 表 (如果id已经存在，数据库会自动跳过)
        insert_query = """
            INSERT IGNORE INTO products_product (id, name, description, price, category, created_at, stock)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (product_id, name, description, price, category, created_at, stock))
        
        # 如果有外键依赖，确保相关表的数据也存在，例如插入 productimage 数据
        # 在这里插入相关的 productimage 数据，例如：
        # insert_product_image_query = """
        #     INSERT INTO products_productimage (product_id, image_url)
        #     VALUES (%s, %s)
        # """
        # cursor.execute(insert_product_image_query, (product_id, 'image_url_here'))

        conn.commit()  # 提交事务
        print(f"成功插入商品: {name} (ID: {product_id})")
    except mysql.connector.Error as err:
        print(f"插入商品 {name} 失败: {err}")
        conn.rollback()  # 如果有错误，回滚事务

# 关闭连接
cursor.close()
conn.close()
