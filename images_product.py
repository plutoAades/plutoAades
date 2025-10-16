import json
from datetime import datetime

# 读取 JSON 文件
with open('dangdang_goods.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取需要的字段并添加当前时间字段
updated_data = []
for item in data:
    updated_item = {
        "product_id": item.get("id"),
        "image": item.get("image_main"),
        "uploaded_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当前时间字段
    }
    updated_data.append(updated_item)

# 打印结果查看
for item in updated_data:
    print(item)

# 如果需要写入新的文件
with open('updated_dangdang_goods.json', 'w', encoding='utf-8') as f:
    json.dump(updated_data, f, ensure_ascii=False, indent=2)
