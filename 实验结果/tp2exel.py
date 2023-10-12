"""
将txt数据转换为xls（表格）文件，方便后面做数据分析
"""

# -*- encoding: utf-8 -*-

import sys
import numpy as np
import os
import xlwt #需要的模块
def txt_xls(dirname,xlsname):
#文本转换成xls的函数
#param filename txt文本文件名称、
#param xlsname 表示转换后的excel文件名
    try:
        filenames = os.listdir(dirname)
        xls=xlwt.Workbook()
        sheet = xls.add_sheet('sheet1',cell_overwrite_ok=True)
        x = 0
        for filename in filenames:
            f = open(dirname + "\\" + filename, encoding = "UTF-8")
            line = f.readline()
            if not line:
                break  #如果没有内容，则退出循环
            arr = line.split(' ')
            arr.pop(-1)
            print(len(arr))
            new_arr = np.array([float(x) for x in arr])
            int_arr = np.trunc(new_arr)
            int_arr.sort()
            sheet.write(0, x, filename[:-4])
            for i in range(len(int_arr)):
                sheet.write(i + 1, x, int_arr[i]) #x单元格经度，i 单元格纬度
            x += 1
            f.close()
        xls.save(xlsname) #保存xls文件
    except:
        raise


if __name__ == "__main__" :
    dirname = sys.argv[1]
    xlsname  = sys.argv[2]
    txt_xls(dirname,xlsname)
