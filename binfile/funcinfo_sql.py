#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:51:35+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: funcinfo_sql.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-02T13:54:20+08:00
# @Copyright: Copyright by USTC

from sql_models import DataDb
from funcinfo_json import FunInfoJson
from functools import wraps

class FunInfoSql(object):
    '''
    函数信息数据库操作类，主要由FunInfoJson和数据库模型类组成
    封装上述两个类的主要功能
    '''
    def __init__(self, filenames, json_names=None):
        '''
        @param filenames 二进制文件名列表,filenames[0]存储原二进制文件名，filenames[1]存储补丁二进制文件名
        @param json_names json文件名列表，json_names[0]存储原json文件名，json_names[1]存储补丁json文件名
        '''
        self.filenames = filenames
        if json_names:
            self.json_names = json_names
            self.funcinfo_json_o = FunInfoJson(filenames[0], jsonname=json_names[0])
            self.funcinfo_json_p = FunInfoJson(filenames[1], isPatch=True, jsonname=json_names[1])
        self.funcinfo_json_o = FunInfoJson(filenames[0])
        self.funcinfo_json_p = FunInfoJson(filenames[1], isPatch=True)

    @classmethod
    def create_db(cls, sql_name=None):
        '''
        建立库表
        '''
        if sql_name:
            cls.sql_name = sql_name
            cls.db = DataDb(cls.sql_name)
        else:
            cls.db = DataDb()

    def check_db(f):
        '''
        修饰器：检查数据库是否存在
        '''
        @wraps
        def decorated(*args, **kwargs):
            self = args[0]
            if not self.db:
                print('database is not exist')
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

    @check_db
    def query_func_info(self, address):
        '''
        查询获取函数信息
        '''

    @check_db
    def query_func_nodes(self, address, isPatch=False):
        '''
        查询获取节点列表
        '''
        _node = self.query_node(address, isPatch)
        funcname = _node.funcname
        nodes = self.db.query_nodes(funcname, isPatch=isPatch, isNode=True)
        return nodes

    @check_db
    def query_node(self, address, isPatch=False):
        '''
        查找单个节点
        '''
        return self.db.query_nodes(address, isPatch)

    @check_db
    def query_func_asms(self, node, isPatch=False):
        '''
        查询获取汇编信息
        '''
        return self.db.query_asms(node, isPatch=False)

    def set_jsonname(self, json_name_o=None, json_name_p=None):
        '''
        设置json文件名
        '''
        if json_name_o:
            self.funcinfo_json_o.jsonname=json_name_o
        if json_name_p:
            self.funcinfo_json_p.jsonname=json_name_p
