#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-29T15:06:07+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: binfile.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-08T15:47:40+08:00
# @Copyright: Copyright by USTC
from bindiffex import BinDiffEx
from funcinfo_sql import FunInfoSql
from func_graph import FuncGraph

import os
import sys
sys.path.append("..")

from setting import BINDIFF, JSONFILE, FUNCINFOSQL

class BinFile(object):
    '''
    二进制处理类，统一整个预处理工作
    负责将二进制文件最总转换成数据库信息存储，并提供函数图类迭代调用
    添加一个函数根据traces获取语义分析前置数据即汇编代码集、基本块首末地址列表
    '''
    def __init__(self, filenames, diff_threshold=1.0, diff_dir=None, sql_name=None,
            json_dir=None, json_names=None, funcinfo_dir=None, funcinfo_name=None):
        '''
        @param filenames 二进制长文件名，长度为2，filenames[0]为原文件，filenames[1]为补丁文件
        @param diff_threshold BinDiff筛选阈值
        @param diff_dir bindiff结果数据库路径
        @param sql_name bindiff结果数据库名称
        @param json_dir 生成json文件目录
        @param json_names 生成json短文件名列表
        @param funcinfo_dir 最终函数信息数据库路径
        '''
        self.filenames = filenames
        self.diff_threshold = diff_threshold
        self.diff_dir = diff_dir
        self.sql_name = sql_name
        self.json_dir = json_dir
        self.json_names = json_names
        self.funcinfo_dir = funcinfo_dir
        self.funcinfo_name = funcinfo_name
        self.cmpedaddrs = None
        self.current_func_index = 0
        self.cur_funcs = None
        self._deault_setting()
        self.funcinfosql_name = os.path.join(self.funcinfo_dir, self.funcinfo_name)
        self.bindiff = BinDiffEx(filenames, diff_dir=self.diff_dir, sql_name=self.sql_name)
        self.funcinfosql = FunInfoSql(filenames, json_dir=self.json_dir, json_names=self.json_names)
        FunInfoSql.create_db(self.funcinfosql_name)

    def _deault_setting(self):
        '''
        检查添加默认配置
        '''
        if self.diff_dir is None:
            self.diff_dir = BINDIFF['DIFF_DIR']
        if self.sql_name is None:
            self.sql_name = BINDIFF['SQL_NAME']
        if self.json_dir is None:
            self.json_dir = JSONFILE['JSON_DIR']
        if self.json_names is None:
            self.json_names = [JSONFILE['JSON_NAME_O'], JSONFILE['JSON_NAME_P']]
        if self.funcinfo_dir is None:
            self.funcinfo_dir = FUNCINFOSQL['FUNC_INFO_DIR']
        if self.funcinfo_name is None:
            self.funcinfo_name = FUNCINFOSQL['FUNC_INFO_NAME']

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
        if self.cmpedaddrs is None:
            self.diff_filter()
        address_o = ','.join(map(lambda x : str(x[0]), self.cmpedaddrs))
        address_p = ','.join(map(lambda x : str(x[1]), self.cmpedaddrs))
        self.funcinfosql.add_data(address_o, isPatch=False)
        self.funcinfosql.add_data(address_p, isPatch=True)

    def get_seman_data(self, nodes_o_list, nodes_p_list, func_o=None, func_=None):
        '''
        根据traces获取语义分析前置数据即汇编代码集、基本块首末地址列表
        @param nodes_o_list 原基本块序列列表
        @type nodes_o_list 列表的列表
        @param nodes_p_list 补丁基本块序列列表
        @type nodes_p_list 列表的列表
        @param func_o 原函数图
        @param func_p 补丁函数图
        '''
        if func_o is None or func_p is None:
            func_o, func_p = self.cur_funcs
        seman_data = []
        for nodes_o, nodes_p in zip(nodes_o_list, nodes_p_list):
            asms_o, addrs_o = self._get_single_smdata(func_o, nodes_o)
            asms_p, addrs_p = self._get_single_smdata(func_p, nodes_p)
            seman_data.append((asms_o, asms_p, addrs_o, addrs_p))
        return seman_data

    def _get_single_smdata(self, func, nodes):
        '''
        获取单个函数语义分析前置数据
        '''
        asms = []
        addres = []
        for n in nodes:
            asms.extend(func.nodes[n]['asms'])
            addr_start = func.nodes[n]['startEA']
            addr_end = func.nodes[n]['endEA']
            addres.append((addr_start, addr_end))
        return asms, addres

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
        self.cur_funcs = (_funcgraph_o, _funcgraph_p)
        return _funcgraph_o, _funcgraph_p

    def next_func_graphs(self):
        '''
        获取函数图对，使用生成器
        '''
        for address_o, address_p in self.cmpedaddrs:
            _funcgraph_o, _funcgraph_p = self.get_single_graphs(address_o, address_p)
            yield _funcgraph_o, _funcgraph_p
            self.current_func_index += 1

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
