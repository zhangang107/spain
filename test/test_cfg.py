#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-07T14:40:12+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_cfg.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-07T21:00:35+08:00
# @Copyright: Copyright by USTC

import sys
import os
sys.path.append("..")
from binfile import BinFile
from cfg import CFG
from setting import BASE_DIR

file_o = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-f')
file_p = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-g')
filenames = [file_o, file_p]

bf = BinFile(filenames)
bf.diff()
print bf.diff_filter()

# import ipdb; ipdb.set_trace()
graph_o, graph_p = bf.next_func_graphs().next()

cfg_o = CFG(func_graph=graph_o)
cfg_p = CFG(func_graph=graph_p)
cfg_o.calculate()
# print cfg_o.nodesXYZ
print cfg_o.get_centroid()
