#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:52:24+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: func_graph.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-02T09:41:54+08:00
# @Copyright: Copyright by USTC
import networkx as nx

class FuncGraph(nx.DiGraph):
    '''
    函数图类
    将函数基本块（即节点）以及汇编信息封装到有向图中,汇编信息存储在节点属性中
    '''
    def __init__(self, name=None):
        if name:
            self.name = name
