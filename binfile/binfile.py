#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:06:07+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: binfile.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-02T15:51:58+08:00
# @Copyright: Copyright by USTC

from bindiffex import BinDiffEx
from funcinfo_sql import FunInfoSql
from func_graph import FuncGraph

class BinFile(object):
    '''
    二进制处理类，统一整个预处理工作
    负责将二进制文件最总转换成数据库信息存储，并提供函数图类迭代调用
    '''
    def __init__(self, filenames, diff_threshold=1.0, diff_path=None, json_path=None,
                    funcinfo_path=None):
        '''
        @param filenames 二进制文件名，长度为2，filenames[0]为原文件，filenames[1]为补丁文件
        @param diff_threshold BinDiff筛选阈值
        @param diff_path bindiff结果数据库路径
        @param json_path json文件路径
        @param funcinfo_path 最终函数信息数据库路径
        '''
        self.filenames = filenames
        self.diff_threshold = diff_threshold
        self.diff_path = diff_path
        self.json_path = json_path
        self.funcinfo_path = funcinfo_path
        self.bindiff = BinDiffEx(filenames, diff_path)
        FunInfoSql.create_db()
        self.funcinfosql = FunInfoSql(filenames)
        self.cmpedaddrs = None

    def diff(self):
        self.bindiff.differ()

    def diff_filter(self, threshold=None):
        if threshold is None:
            threshold = self.diff_threshold
        self.bindiff.getcmped(threshold)
        self.cmpedaddrs = self.bindiff.cmpedaddrs
        return len(self.cmpedaddrs)

    def init_funcinfo(self):
        '''
        根据bindiff筛选结果生成函数信息数据库
        '''
        address_o = ','.join(map(lambda x : str(x[0]), self.cmpedaddrs))
        address_p = ','.join(map(lambda x : str(x[1]), self.cmpedaddrs))
        self.funcinfosql.add_data(address_o, isPatch=False)
        self.funcinfosql.add_data(address_p, isPatch=True)

    def _get_single_graph(self, address, isPatch):
        '''
        获取一个函数图
        @param address 函数地址
        @param isPatch 是否是补丁
        '''
        nodes, edges, funcname = self.funcinfosql.query_func_info(address_o, isPatch)
        _funcgraph = FuncGraph(funcname, nodes, edges)
        return _funcgraph

    def get_single_graphs(self, address_o, address_p):
        '''
        获取单对函数图
        @param address_o 原函数地址
        @param address_p 补丁函数地址
        '''
        _funcgraph_o = self._get_single_graph(address_o, isPatch=False)
        _funcgraph_p = self._get_single_graph(address_p, isPatch=True)
        return _funcgraph_o, _funcgraph_p

    def get_func_graphs(self):
        '''
        获取函数图对，使用生成器
        '''
        for address_o, address_p in self.cmpedaddrs:
            _funcgraph_o, _funcgraph_p = self.get_single_graphs(address_o, address_p)
            yield _funcgraph_o, _funcgraph_p
