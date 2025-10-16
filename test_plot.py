import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
structure = {
    "系统功能": {
        "普通用户模块": [
            "用户注册与登录",
            "商品浏览与搜索",
            "商品详情与评价",
            "购物车功能",
            "订单管理",
            "实时沟通"
        ],
        "管理员模块": [
            "商品管理",
            "用户管理",
            "订单管理",
            "数据可视化统计",
            "系统管理"
        ],
        "数据采集与分析模块": [
            "数据采集",
            "数据处理",
            "数据对比与分析",
            "数据可视化"
        ],
        "聊天模块": [
            "实时消息传递",
            "消息存储与查询",
            "多会话支持",
            "消息提醒"
        ]
    }
}
# 把文字转为竖排（逐字换行）
def vertical_text(text):
    return "\n".join(list(text))
# 计算每个节点的子树叶子数
def count_leaves(node):
    if isinstance(node, list):
        return len(node)
    elif isinstance(node, dict):
        return sum(count_leaves(v) for v in node.values())
    else:
        return 1
# 绘制组织结构图
def draw_tree(node, x, y, x_range, parent=None, vertical_children=False):
    if isinstance(node, dict):
        leaves = count_leaves(node)
        step = x_range / leaves
        cur_x = x - x_range/2 + step/2
        for key, child in node.items():
            child_leaves = count_leaves(child)
            child_range = step * child_leaves
            child_x = cur_x + child_range/2 - step/2
            child_y = y - 1.8
            # 父节点还是横着的长方形
            plt.text(child_x, child_y, key, ha="center", va="center",
                     fontsize=10,
                     bbox=dict(boxstyle="square,pad=0.6", fc="lightblue", ec="black"))
            # 画线
            if parent:
                px, py = parent
                plt.plot([px, px], [py-0.2, py-0.8], "k-")
                plt.plot([px, child_x], [py-0.8, py-0.8], "k-")
                plt.plot([child_x, child_x], [py-0.8, child_y+0.2], "k-")
            # 子节点要求竖排
            draw_tree(child, child_x, child_y, child_range, (child_x, child_y), vertical_children=True)
            cur_x += child_range
    elif isinstance(node, list):
        step = x_range / len(node)
        cur_x = x - x_range/2 + step/2
        for item in node:
            child_x = cur_x
            child_y = y - 1.8
            # 子节点竖长方形 + 文字竖排
            plt.text(child_x, child_y, vertical_text(item), ha="center", va="center",
                     fontsize=9,
                     bbox=dict(boxstyle="square,pad=0.6", fc="white", ec="black"))
            # 画线
            if parent:
                px, py = parent
                plt.plot([px, px], [py-0.2, py-0.8], "k-")
                plt.plot([px, child_x], [py-0.8, py-0.8], "k-")
                plt.plot([child_x, child_x], [py-0.8, child_y+0.2], "k-")
            cur_x += step
plt.figure(figsize=(14, 8))
root = list(structure.keys())[0]
plt.text(0.5, 1, root, ha="center", va="center",
         fontsize=12,
         bbox=dict(boxstyle="square,pad=0.8", fc="lightgreen", ec="black"))
draw_tree(structure[root], 0.5, 1, 1.0, parent=(0.5, 1))
plt.axis("off")
# plt.title("系统功能结构图", fontsize=14)
plt.tight_layout()
plt.show()
