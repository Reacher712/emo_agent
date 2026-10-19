# -*- coding: utf-8 -*-
"""生成情感疗愈小节图表：抑郁患病率 + 精神科医师密度"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 数据：国家, 抑郁患病率(%), 精神科医师(每10万人)
# 来自PDF: Argentina, Australia, Bangladesh, Belarus, Belgium, Brazil
# 补充关键国家(WHO Mental Health Atlas/IHME典型值): China, USA, Japan, India
data = [
    ("中国", 3.0, 2.2),      # WHO Atlas 2017; 抑郁率约3%
    ("印度", 3.9, 0.3),      # WHO; 资源极低
    ("美国", 4.7, 15.1),     # WHO GHO
    ("日本", 3.4, 11.7),     # WHO
    ("巴西", 5.8, 3.2),      # PDF
    ("澳大利亚", 5.9, 13.5),  # PDF
    ("比利时", 4.8, 20.1),   # PDF
    ("阿根廷", 4.7, 21.7),   # PDF
    ("孟加拉国", 4.1, 0.13), # PDF
]

countries = [d[0] for d in data]
depression = [d[1] for d in data]
psychiatrists = [d[2] for d in data]

fig, ax1 = plt.subplots(figsize=(10, 6))

x = range(len(countries))
width = 0.35

# 左轴：抑郁患病率（柱状图）
bars1 = ax1.bar([i - width/2 for i in x], depression, width, label='抑郁患病率 (%)', color='#4A90D9', alpha=0.8)
ax1.set_ylabel('抑郁患病率 (%)', fontsize=11)
ax1.set_ylim(0, 7)
ax1.tick_params(axis='y')

# 右轴：精神科医师密度（柱状图）
ax2 = ax1.twinx()
bars2 = ax2.bar([i + width/2 for i in x], psychiatrists, width, label='精神科医师（每10万人）', color='#E67E22', alpha=0.8)
ax2.set_ylabel('精神科医师（每10万人）', fontsize=11)
ax2.set_ylim(0, 25)
ax2.tick_params(axis='y')

# 设置x轴
ax1.set_xticks(x)
ax1.set_xticklabels(countries, rotation=30, ha='right')

# 标题与图例
ax1.set_title('各国抑郁患病率与心理健康资源配置对比\n数据来源：WHO GHO (2015-2017)', fontsize=12)
fig.legend(loc='upper right', bbox_to_anchor=(0.88, 0.88), fontsize=9)

plt.tight_layout()
out_path = r'D:\moxin\mental_health_chart.png'
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f'已保存: {out_path}')
plt.close()
