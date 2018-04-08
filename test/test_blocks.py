#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-07T21:06:20+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_blocks.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-07T21:10:07+08:00
# @Copyright: Copyright by USTC

import sys
import os
sys.path.append("..")
from binfile import BinFile
from block import Trace
from setting import BASE_DIR

file_o = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-f')
file_p = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-g')
filenames = [file_o, file_p]

bf = BinFile(filenames)
bf.diff()
print bf.diff_filter()

# import ipdb; ipdb.set_trace()
graph_o, graph_p = bf.next_func_graphs().next()

t = Trace(graph_o=graph_o, graph_p=graph_p)
print t.get_trace()
