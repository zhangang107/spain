#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:51:35+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: funcinfo_sql.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-19T15:25:14+08:00
# @Copyright: Copyright by USTC

from sql_models import DataDb
from funcinfo_json import FunInfoJson, comlog
from functools import wraps
import os

def _cumulate_item(item_list):
    '''
    统计
    '''
    item_dic = {}
    for item in item_list:
        if item not in item_dic:
            item_dic[item] = 1
        else:
            item_dic[item] += 1
    return item_dic

def _handle_call(mnem_list, opnds_list):
    '''
    识别并统计跳转指令
    '''
    # arm call
    call_dic = {}
    for i in range(len(mnem_list)):
        if mnem_list[i] == 'BL':
            if 'BL' not in call_dic:
                call_dic['BL'] = [opnds_list[i]]
            else:
                call_dic['BL'].append(opnds_list[i])
    return call_dic

class FunInfoSql(object):
    '''
    函数信息数据库操作类，主要由FunInfoJson和数据库模型类组成
    封装上述两个类的主要功能
    '''
    def __init__(self, filenames, json_dir=None, json_names=None):
        '''
        @param filenames 二进制文件名列表,filenames[0]存储原二进制文件名，filenames[1]存储补丁二进制文件名
        @param json_dir 生成的json文件目录
        @param json_names json短文件名列表，json_names[0]存储原json文件名，json_names[1]存储补丁json文件名
        '''
        self.filenames = filenames
        self.funcinfo_json_o = FunInfoJson(filenames[0], json_name=json_names[0], json_dir=json_dir)
        self.funcinfo_json_p = FunInfoJson(filenames[1], isPatch=True, json_name=json_names[1], json_dir=json_dir)

    @classmethod
    def create_db(cls, sql_name=None):
        '''
        建立库表
        '''
        # 添加删除存在的旧库
        if os.path.isfile(sql_name):
            os.remove(sql_name)
        cls.db = DataDb(sql_name)
        cls.db.create_tb()

    def check_db(f):
        '''
        修饰器：检查数据库是否存在
        '''
        @wraps(f)
        def decorated(*args, **kwargs):
            self = args[0]
            if not self.db:
                comlog.error('database is not exist')
                return None
            return f(*args, **kwargs)
        return decorated

    @check_db
    def json2sql(self, isPatch=False):
        '''
        将json文件写入数据库
        '''
        if isPatch:
            self.funcinfo_json_p.json2sql(self.db)
        else:
            self.funcinfo_json_o.json2sql(self.db)


    @check_db
    def add_data(self, address_str, isPatch=False):
        '''
        将二进制文件写入json文件数据在写入数据库
        '''
        if isPatch:
            self.funcinfo_json_p.write_func(address_str, self.db)
        else:
            self.funcinfo_json_o.write_func(address_str, self.db)

    def _get_func_info(self, _nodes, funcname, isPatch=False):
        '''
        依据数据库结果_nodes，构造函数图类所需节点nodes,边edges,以及函数名
        '''
        edges = []
        nodes = {}
        for _n in _nodes:
            src = _n.block_id
            for dst in eval(_n.child):
                edges.append([src, int(dst)])
            nodes[src] = {'funcname':funcname, 'startEA': _n.block_start,
                            'endEA':_n.block_end}
            _asms = self.query_node_asms(_n, isPatch)
            # if funcname.encode('utf-8') == 'req_main' and isPatch and _n.block_id==412:
            #         # print _n.block_id
            #         import ipdb; ipdb.set_trace()
            asms, sizes, mnem_list, opnds_list, optype_list = [], [], [], [], []
            for a in _asms:
                asms.append(a.asm.encode('utf-8'))
                sizes.append(a.size)
                mnem_list.append(a.mnem.encode('utf-8'))
                opnds_list.append(a.opnds.encode('utf-8'))
                optype_list.append(a.optypes.encode('utf-8'))
            nodes[src]['asms'] = asms
            nodes[src]['sizes'] = sizes
            nodes[src]['power'] = len(asms)
            nodes[src]['mnem'] = _cumulate_item(mnem_list)
            nodes[src]['mnem_list'] = mnem_list
            nodes[src]['optype'] = _cumulate_item(optype for optlist in optype_list for
                                            optype in eval(optlist))
            nodes[src]['call'] = _handle_call(mnem_list, opnds_list)
        address = nodes[0]['startEA']
        return funcname, address, nodes, edges

    @check_db
    def query_func_info(self, arg, isPatch=False):
        '''
        查询获取函数信息，获取边以及各个节点内部汇编信息
        @arg 不定参数   当arg为int时，即是地址address
                       当arg为str时，即是函数名funcname
        '''
        if isinstance(arg, int):
            address = arg
            _nodes, funcname = self.query_func_nodes(address, isPatch)
            return self._get_func_info(_nodes, funcname, isPatch=isPatch)
        elif isinstance(arg, str):
            funcname = arg
            _nodes = self.db.query_nodes(funcname, isPatch=isPatch, isNodes=True)
            return self._get_func_info(_nodes, funcname, isPatch=isPatch)

    @check_db
    def query_func_nodes(self, address, isPatch=False):
        '''
        查询获取节点列表
        '''
        _node = self.query_node(address, isPatch)
        funcname = _node.funcname.encode('utf-8')
        nodes = self.db.query_nodes(funcname, isPatch=isPatch, isNodes=True)
        return nodes, funcname

    @check_db
    def query_node(self, address, isPatch=False):
        '''
        查找单个节点
        '''
        return self.db.query_nodes(address, isPatch)

    @check_db
    def query_node_asms(self, node, isPatch=False):
        '''
        查询获取节点汇编信息
        '''
        return self.db.query_asms(node, isPatch=isPatch)

    def set_jsonname(self, json_name_o=None, json_name_p=None):
        '''
        设置json文件名
        '''
        if json_name_o:
            self.funcinfo_json_o.jsonname=json_name_o
        if json_name_p:
            self.funcinfo_json_p.jsonname=json_name_p
