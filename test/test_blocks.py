#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-07T21:06:20+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_blocks.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-18T16:09:48+08:00
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
# bf.diff()
print bf.diff_filter()
# bf.init_funcinfo()
# import ipdb; ipdb.set_trace()
# for graph_o, graph_p in bf.next_func_graphs():
#     print graph_o.funcname
#     t = Trace(graph_o=graph_o, graph_p=graph_p)
#     print t.get_trace()
#     print t.traces2nodes()
'''
貌似要修改匹配正确率
'''
graph_o, graph_p = bf.get_func_graphs('dtls1_process_heartbeat')
t = Trace(graph_o, graph_p)
print t.get_trace()
print t.traces2nodes()
