#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:06:07+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: binfile.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-04T09:53:32+08:00
# @Copyright: Copyright by USTC

from bindiffex import BinDiffEx
from funcinfo_sql import FunInfoSql
from func_graph import FuncGraph

class BinFile(object):
    '''
    二进制处理类，统一整个预处理工作
    负责将二进制文件最总转换成数据库信息存储，并提供函数图类迭代调用
    '''
    def __init__(self, filenames, diff_threshold=1.0, diff_dir=None, sql_name=None,
            json_path=None, funcinfo_path=None):
        '''
        @param filenames 二进制文件名，长度为2，filenames[0]为原文件，filenames[1]为补丁文件
        @param diff_threshold BinDiff筛选阈值
        @param diff_dir bindiff结果数据库路径
        @param sql_name bindiff结果数据库名称
        @param json_path json文件路径
        @param funcinfo_path 最终函数信息数据库路径
        '''
        self.filenames = filenames
        self.diff_threshold = diff_threshold
        self.diff_dir = diff_dir
        self.json_path = json_path
        self.funcinfo_path = funcinfo_path
        self.bindiff = BinDiffEx(filenames, diff_dir=diff_dir, sql_name=sql_name)
        FunInfoSql.create_db()
        self.funcinfosql = FunInfoSql(filenames)
        self.cmpedaddrs = None
        self.current_func = 0

    def diff(self):
        '''
        完成IDC调用和BinDiff调用，生成BinDiff数据库
        '''
        self.bindiff.differ()

    def diff_filter(self, threshold=None):
        '''
        bindiff筛选，获取初始候选函数对
        '''
        if threshold is None:
            threshold = self.diff_threshold
        self.cmpedaddrs = self.bindiff.getcmped(threshold)
        return len(self.cmpedaddrs)

    def init_funcinfo(self):
        '''
        根据bindiff筛选结果生成函数信息数据库
        '''
        address_o = ','.join(map(lambda x : str(x[0]), self.cmpedaddrs))
        address_p = ','.join(map(lambda x : str(x[1]), self.cmpedaddrs))
        self.funcinfosql.add_data(address_o, isPatch=False)
        self.funcinfosql.add_data(address_p, isPatch=True)

    def _get_single_graph(self, arg, isPatch):
        '''
        获取一个函数图
        @param arg 函数地址或者函数名称
        @param isPatch 是否是补丁
        '''
        funcname, address, nodes, edges = self.funcinfosql.query_func_info(arg, isPatch)
        _funcgraph = FuncGraph(funcname, address, nodes, edges)
        return _funcgraph

    def get_single_graphs(self, arg_o, arg_p):
        '''
        获取单对函数图
        @param arg_o 原函数地址或者函数名称
        @param arg_p 补丁函数地址或函数名称
        '''
        _funcgraph_o = self._get_single_graph(arg_o, isPatch=False)
        _funcgraph_p = self._get_single_graph(arg_p, isPatch=True)
        return _funcgraph_o, _funcgraph_p

    def next_func_graphs(self):
        '''
        获取函数图对，使用生成器
        '''
        for address_o, address_p in self.cmpedaddrs:
            _funcgraph_o, _funcgraph_p = self.get_single_graphs(address_o, address_p)
            yield _funcgraph_o, _funcgraph_p
            self.current_func += 1

    def _get_func_by_name(self, name):
        '''
        通过函数名称获取指定函数图对
        '''
        _funcgraph_o, _funcgraph_p = self.get_single_graphs(name, name)
        return _funcgraph_o, _funcgraph_p

    def _get_func_by_index(self, index):
        '''
        通过函数在初始候选中的索引获取函数图对
        '''
        address_o, address_p = self.cmpedaddrs[index]
        _funcgraph_o, _funcgraph_p = self.get_single_graphs(address_o, address_p)
        return _funcgraph_o, _funcgraph_p

    def get_func_graphs(self, arg):
        '''
        获取指定函数图对
        当arg为int时，通过索引指定
        当arg为str时，通过函数名称指定
        '''
        if isinstance(arg, int):
            return self._get_func_by_index(arg)
        elif isinstance(arg, str):
            return self._get_func_by_name(arg)
