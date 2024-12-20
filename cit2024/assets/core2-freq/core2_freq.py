import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np
import pandas as pd


# bins: 设置直方图条形的数目
# is_hist: 是否绘制直方图
# is_kde: 是否绘制核密度图
# is_rug: 是否绘制生成观测数值的小细条
# is_vertical: 如果为True，观察值在y轴上
# is_norm_hist: 如果为True，直方图高度显示一个密度而不是一个计数，如果kde设置为True，则此参数一定为True
def draw_distribution_histogram(nums, path, color, is_hist=True, is_kde=True, is_rug=False, \
    is_vertical=False, is_norm_hist=False):
    
    ax = sns.distplot(nums, bins=20, hist=False, kde=is_kde, rug=is_rug, \
      hist_kws={"color": color}, kde_kws={"color": color}, \
      vertical=is_vertical, norm_hist=is_norm_hist)
    kde_x, kde_y = ax.lines[-1].get_data()
    ax.fill_between(kde_x, kde_y, interpolate=True, color=color, alpha=0.5)
    
  
def get_data(path):
    with open(path, 'r') as f:
        content = f.read()
    result_list = [x for x in content.split("\n")]
    result_list.pop(-1)
    result = np.array([float(x) for x in result_list])
    return result

path = "../prio-core2.pdf"

# Canvas configurations
matplotlib.rcParams['font.family'] = 'Arial'
matplotlib.rcParams['font.size'] = 24

import matplotlib.pyplot as plt


# 代码中的“...”代表省略的其他参数
ax = plt.subplot(111)

# 设置刻度字体大小
plt.xticks(fontsize=24)
plt.yticks(fontsize=24)
# 设置坐标标签字体大小
ax.set_xlabel(..., fontsize=24)
ax.set_ylabel(..., fontsize=24)

# sns.set()  #切换到sns的默认运行配置
sns.set_theme(style="whitegrid", palette="pastel")
# sns.set_palette("husl")


draw_distribution_histogram(get_data("p0.dat"), path, "#9804d4", True, True)
draw_distribution_histogram(get_data("p1.dat"), path, "#009e73", True, True)
draw_distribution_histogram(get_data("p2.dat"), path, "#56b4e9", True, True)
draw_distribution_histogram(get_data("p3.dat"), path, "#e69f00", True, True)

#添加x轴和y轴标签
plt.xlabel("Message Latency(" + r"$\mu$" + "s)")
plt.ylabel("Density")
plt.xlim([0, 900000])
plt.ylim([0, 0.000008])

children = plt.gca().get_children()
keys = []
for idx, val in enumerate(children):
    if idx & 1 != 0:
        keys.append(val)

ax = plt.gca()#获取边框
ax.ticklabel_format(style='sci', scilimits=(-1,2), axis='x')

ax.ticklabel_format(style='sci', scilimits=(-1,2), axis='y')
ax.get_yaxis().get_offset_text().set(va='top', ha='left')
ax.spines['top'].set_color('none')  # 设置上‘脊梁’为红色
ax.spines['right'].set_color('none')  # 设置上‘脊梁’为无色
ax.spines['bottom'].set_color('none')  # 设置下‘脊梁’为无色
ax.spines['left'].set_color('none')  # 设置左‘脊梁’为无色

box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width , box.height* 0.5])
plt.grid(False)
plt.grid(axis='y', linestyle='dotted') # 设置 y 就在轴方向显示网格线
plt.legend(
    keys, 
    ["p0", "p1", "p2", "p3"], 
    frameon=False, 
    loc="upper center", 
    bbox_to_anchor=(0.6, 1.12),
    prop = {'size':24}, 
    ncol=4, 
    handletextpad=0.1, 
    handleheight=0.5, 
    handlelength=1, 
    columnspacing=1
)
plt.tight_layout()  # 处理显示不完整的问题
plt.savefig(path, dpi=300)