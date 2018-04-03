#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:52:24+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: func_graph.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-02T14:47:23+08:00
# @Copyright: Copyright by USTC
import networkx as nx

class FuncGraph(nx.DiGraph):
    '''
    函数图类
    将函数基本块（即节点）以及汇编信息封装到有向图中,汇编信息存储在节点属性中
    '''
    def __init__(self, funcname, nodes=None, edges=None):
        self.funcname = funcname
        self._nodes = nodes
        self._edges = edges
        if nodes and edges:
            self._create(nodes, edges)

    def _create(self, nodes, edges):
        '''
        依据节点和边快速创建函数图
        '''
        self.add_nodes_from(nodes)
        for node_id in nodes:
            self.nodes[node_id].update(nodes[node_id])
        self.add_edges_from(edges)
