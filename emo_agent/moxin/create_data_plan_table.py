# -*- coding: utf-8 -*-
"""生成国画数据收集规划矩阵表"""
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "数据收集规划"

# 数据：6组东方美学坐标，山水画/花鸟画计划幅数
# 总计约1000幅，每格约83幅，适当调整使总和=1000
data = [
    ("豪放-婉约", 85, 82),
    ("空寂-喧闹", 84, 84),
    ("超脱-入世", 83, 83),
    ("疏-密", 84, 83),
    ("虚-实", 83, 84),
    ("淡-浓", 84, 85),
]

# 表头
headers = ["东方美学情感坐标", "山水画（计划幅数）", "花鸟画（计划幅数）"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = Font(bold=True, size=11)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")

# 数据行
for row_idx, (coord, shanshui, huaniao) in enumerate(data, 2):
    ws.cell(row=row_idx, column=1, value=coord)
    ws.cell(row=row_idx, column=2, value=shanshui)
    ws.cell(row=row_idx, column=3, value=huaniao)

# 合计行
ws.cell(row=8, column=1, value="合计")
ws.cell(row=8, column=2, value=sum(d[1] for d in data))
ws.cell(row=8, column=3, value=sum(d[2] for d in data))
for col in range(1, 4):
    ws.cell(row=8, column=col).font = Font(bold=True)

# 边框
thin = Side(style="thin")
for row in range(1, 9):
    for col in range(1, 4):
        ws.cell(row=row, column=col).border = Border(
            left=thin, right=thin, top=thin, bottom=thin
        )

# 对齐
for row in range(1, 9):
    for col in range(1, 4):
        ws.cell(row=row, column=col).alignment = Alignment(
            horizontal="center" if col > 1 else "left",
            vertical="center",
        )

# 列宽
ws.column_dimensions["A"].width = 18
ws.column_dimensions["B"].width = 18
ws.column_dimensions["C"].width = 18

out_path = r"D:\moxin\data_collection_plan.xlsx"
wb.save(out_path)
print(f"已保存: {out_path}")
