#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T16:43:00+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_binfile.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-04T20:57:42+08:00
# @Copyright: Copyright by USTC
import sys
import os
sys.path.append("..")
from binfile import BinFile
from setting import BASE_DIR

file_o = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-f')
file_p = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-g')
filenames = [file_o, file_p]

bf = BinFile(filenames)
bf.diff()
print bf.diff_filter()
bf.init_funcinfo()
import ipdb; ipdb.set_trace()
