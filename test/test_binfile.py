#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T16:43:00+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_binfile.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-04T10:14:11+08:00
# @Copyright: Copyright by USTC
import sys
import os
sys.path.append("..")
from binfile import BinFile

cwd = os.getcwd()
# print cwd.split()
file_o = os.path.join(cwd, '../../data/tmp/openssl-arm-f')
file_p = os.path.join(cwd, '../../data/tmp/openssl-arm-g')

filenames = [file_o, file_p]
diff_dir = os.path.join(cwd, '../../data/result/')
sql_name = 'diff.db'

bf = BinFile(filenames,diff_dir=diff_dir, sql_name=sql_name)
# bf.diff()
print bf.diff_filter()
