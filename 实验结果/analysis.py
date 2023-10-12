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
            a = filename.split('-')
            count = int(a[1][:-4])
            sheet.write(x, 0, a[0])
            # print(a[0], count)
            f = open(dirname + "\\" + filename, encoding = "UTF-8")
            line = f.readline()
            if not line:
                break  #如果没有内容，则退出循环
            arr = line.split(' ')
            arr.pop(-1)
            print(len(arr))
            new_arr = np.array([float(x) for x in arr])
            mean = np.mean(new_arr)
            std = np.std(new_arr)

            sheet.write(x, 1, new_arr.size / count)
            sheet.write(x, 2, mean)
            sheet.write(x, 3, std)
    
            x += 1
            f.close()
        xls.save(xlsname) #保存xls文件
    except:
        raise


if __name__ == "__main__" :
    dirname = sys.argv[1]
    xlsname  = sys.argv[2]
    txt_xls(dirname,xlsname)