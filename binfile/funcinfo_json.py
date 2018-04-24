#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:51:07+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: funcinfo_json.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-24T09:54:01+08:00
# @Copyright: Copyright by USTC

from sql_models import tb_nodes_o, tb_nodes_p, tb_asms_o, tb_asms_p
import os
import commands
import json

from spain import BASE_DIR, comlog

class FunInfoJson(object):
    '''
    函数信json操作类
    主要功能:
        完成IDAPython脚本调用，从IDA中获取函数信息，包括节点信息和汇编信息
        将json文件写入数据库
    提供的外部调用为：
        二进制文件到函数信息数据库
    '''
    script = os.path.join(BASE_DIR, 'spain/binfile/idaPython/getinfo_fromIDA.py')
    def __init__(self, filename, isPatch=False, json_name=None, json_dir=None):
        '''
        @param filename 二进制长文件名
        @param isPatch 是否是补丁文件
        @param json_name 生成的json文件名
        @param json_dir 生成json文件目录
        '''
        self.filename = filename
        self.exefilename = self._split_file()
        self.json_dir = json_dir
        self.json_name = json_name
        self.isPatch = isPatch
        self._default()


    def _default(self):
        if self.json_dir is None:
            self.json_dir = os.path.join(BASE_DIR, 'data/output/')
        if self.json_name is None:
            if self.isPatch:
                self.json_name = 'func_p.json'
            else:
                self.json_name = 'func_o.json'
        if self.isPatch:
            self.tb_nodes = tb_nodes_p
            self.tb_asms = tb_asms_p
        else:
            self.tb_nodes = tb_nodes_o
            self.tb_asms = tb_asms_o

    def _split_file(self):
        '''
        分解文件名
        '''
        _, exefilename = os.path.split(self.filename)
        return exefilename

    def _IDAPython_call(self, address_str):
        '''
        调用IDAPython
        @param address: ida脚本参数 函数首地址字符串
        '''
        self.out_json = os.path.join(self.json_dir, self.json_name)
        cmd = "TVHEADLESS=1 idal -A -S'{} {} {}' {} > /dev/null".format(self.script, \
                    address_str, self.out_json, self.filename)
        comlog.debug(cmd)
        (status, output) = commands.getstatusoutput(cmd) # output 做debug用
        if status != 0: # 正常返回0
            comlog.error('IDAPython call error')
            comlog.error('error info: {}'.format(output))
        return status

    def _check_file(self):
        '''
        检查文件是否存在
        '''
        exist = True
        try:
            f = open(self.out_json)
            f.close()
        except Exception as err:
            exist = False
            comlog.error("[error] {} not exist, something wrong".format(self.out_json))
            comlog.error('error info: {}'.format(err))
        return exist

    def json2sql(self, db):
        '''
        将json文件写入数据库
        @param db 数据库模型实例
        '''
        def _con2str(d):
            for i in d:
                if isinstance(d[i], list):
                    d[i] = str(d[i])
        if self._check_file():
            f = open(self.out_json)
            nodes = []
            asms = []
            data = json.load(f)
            f.close()
            funcs = data['funcs']
            for func in funcs:
                name = func['funcname']
                nodes_data = func['nodes']
                for d in nodes_data:
                    _con2str(d)
                    d['funcname'] = name
                nodes.extend(nodes_data)
                asms_data = func['asms']
                for d in asms_data:
                    _con2str(d)
                    d['oplen'] = len(d['opnds'])
                asms.extend(asms_data)
                # if name.encode('utf-8') == 'req_main' and self.isPatch:
                    # import ipdb; ipdb.set_trace()
            db.add_data(self.tb_nodes, nodes)
            db.add_data(self.tb_asms, asms)

    def write_func(self, address_str, db):
        '''
        完成从二进制文件到函数信息数据库,即封装self._IDAPython_call 和self._json2sql
        @param address: ida脚本参数 函数首地址字符串
        @param db 数据库模型实例
        '''
        self._IDAPython_call(address_str)
        self.json2sql(db)
