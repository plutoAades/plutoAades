import subprocess
import sys
import os

def run_script(script_name):
    """运行指定 Python 脚本"""
    try:
        print(f"正在执行 {script_name} ...")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"✅ {script_name} 执行完成\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: {script_name} 执行失败. 错误: {e}")
        exit(1)

if __name__ == "__main__":
    scripts = [
        ("data_collect.py", None),
        ("images_product.py", "dangdang_goods.json"),
        ("product_collectjson.py", "dangdang_goods.json"),
    ]

    for script, depend_file in scripts:
        # 如果有依赖文件，先检查是否存在
        if depend_file and not os.path.exists(depend_file):
            print(f"⚠️ 跳过 {script}，因为依赖文件 {depend_file} 不存在")
            break
        run_script(script)
