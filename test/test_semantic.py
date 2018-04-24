#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-08T14:44:32+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: test_semantic.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-23T17:00:50+08:00
# @Copyright: Copyright by USTC

import sys
import os
sys.path.append("..")
from binfile import BinFile
from seman import Semantic
from block import Trace
from setting import BASE_DIR

file_o = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-f')
file_p = os.path.join(BASE_DIR, 'data/binfile/openssl-arm-g')
filenames = [file_o, file_p]

bf = BinFile(filenames)
bf.diff()
print bf.diff_filter()
bf.init_funcinfo()

# import ipdb; ipdb.set_trace()
# graph_o, graph_p = bf.next_func_graphs().next()
#
# nodes_o_list = [[1, 2, 3], [7, 8, 9]]
# nodes_p_list = [[1, 2, 3], [7, 8, 9]]
# sem_data = bf.get_seman_data(nodes_o_list, nodes_p_list)
# print sem_data
# '''
# 测试语义分析
# '''
# asms_o = None
# asms_p = None
# addrs_o = None
# addrs_o = None
# sim = Semantic(*sem_data[0], load_args=filenames)
# print sim.get_pre_state()
# print sim.get_post_state()
# print sim.get_semidiff()

graph_o, graph_p = bf.get_func_graphs('tls1_process_heartbeat')
t = Trace(graph_o, graph_p)
trace = t.get_trace()
nodes = t.traces2nodes()
sem_data = bf.get_seman_data(*nodes)
for _sem in sem_data:
    sim = Semantic(*_sem[0:4], load_args=filenames)
    print '---------------pre_state---------------------'
    print sim.get_pre_state()
    print '---------------post_state---------------------'
    print sim.get_post_state()
    print '---------------diff---------------------------'
    print sim.get_semidiff()
