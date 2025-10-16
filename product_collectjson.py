import json
from datetime import datetime

# 读取 JSON 文件
with open('dangdang_goods.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 清洗不需要字段；删除不需要的字段
for item in data:
    item.pop('image_main', None)
    item.pop('detail_images', None) 
    item.pop('page', None)
    
    # 添加 created_at 和 stock 字段
    item['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    item['stock'] = 100

# 打印结果查看
for item in data:
    print(item)

# 如果需要写入新的文件
with open('cleaned_dangdang_goods.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

