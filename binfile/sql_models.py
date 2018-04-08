#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T10:20:13+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: sql_models.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-07T14:09:06+08:00
# @Copyright: Copyright by USTC

from sqlalchemy import Column, String, Integer, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

'''
封装方法，隐藏数据库
数据库中的表名对上层是可见的或者封装表名
提供方法：
    建库表
    表数据插入
    查询
    范围查询
'''

'''
数据的表名
'''
# 原始二进制函数节点表
tb_nodes_o = 'nodeso'
# 原始二进制函数汇编表
tb_asms_o = 'funcasmo'
# 补丁二进制函数节点表
tb_nodes_p = 'nodesp'
# 补丁二进制函数汇编表
tb_asms_p = 'funcasmp'

Base = declarative_base()
class DataDb(object):
    def __init__(self, dbstring=None):
        self.dbstring = dbstring
        if self.dbstring is None:
            self.dbstring = 'sqlite:///test_json.db'
        else:
            self.dbstring = 'sqlite:///{}'.format(self.dbstring)
        self.engine = create_engine(self.dbstring)
        self.DBSession = sessionmaker(bind=self.engine)
        # self.session = self.DBSession()
        self.tbs_dict = {tb_nodes_o : NodeO, tb_nodes_p : NodeP,
                        tb_asms_o : FuncAsmO, tb_asms_p : FuncAsmP}

    def create_tb(self):
        Base.metadata.create_all(self.engine)

    def add_data(self, tbname, data):
        '''
        添加数据
        @param tbname 表名
        @parma data 插入的数据 字典列表
        '''
        tb = self._get_tb_byname(tbname)
        session = self.DBSession()
        session.execute(tb.__table__.insert(), data)
        session.commit()

    def _query_range(self, tbname, k, lv, rv):
        '''
        范围查询
        @param tbname 要查询的表
        @param k 查询的关键
        @param lv 范围左端
        @param rv 范围右端
        '''
        session = self.DBSession()
        rs = session.query(tbname).filter(text("{0} >=:lv and {0}<:rv".format(k))).params(lv=lv,
                    rv=rv)
        session.close()
        return rs

    def _query(self, tbname, sql):
        '''
        查询
        '''
        session = self.DBSession()
        rs = session.query(tbname).filter(sql)
        session.close()
        return rs

    def query_nodes(self, arg, isPatch=False, isNodes=False):
        '''
        查询节点或节点集
        @arg 查询参数，地址或函数名称
        @isPatch 是否是查询补丁表
        @isNodes 是否是查询节点集
        '''
        if isPatch:
            tbname = NodeP
        else:
            tbname = NodeO
        if isNodes:
            nodes = self._query(tbname, tbname.funcname==arg).all()
            return nodes
        else:
            node = self._query(tbname, tbname.block_start==arg).one()
            return node

    def query_asms(self, node, isPatch):
        '''
        查询基本快汇编汇编信息
        @parma 节点
        @parma 是否是查询补丁表
        '''
        if isPatch:
            tbname = FuncAsmP
        else:
            tbname = FuncAsmO
        asms = self._query_range(tbname, tbname.address,
                node.block_start, node.block_end).all()
        return asms

    def _get_tb_byname(self, tbname):
        return self.tbs_dict[tbname]

class Node(object):
    '''
    节点表结构
    '''

    id = Column(Integer, primary_key=True, autoincrement=True)
    funcname = Column(String)
    block_id = Column(Integer)
    block_start = Column(Integer)
    block_end = Column(Integer)
    child = Column(String)

    def __init__(self, node):
        if isinstance(node, dict):
            self.funcname = node['funcname']
            self.block_id = node['block_id']
            self.block_start = node['block_start']
            self.block_end = node['block_end']
            self.child = node['child']

class NodeO(Node, Base):
    '''
    原始节点表
    '''
    __tablename__ = tb_nodes_o

class NodeP(Node, Base):
    '''
    补丁节点表
    '''
    __tablename__ = tb_nodes_p

class FuncAsm(object):
    '''
    函数汇编信息表结构
    '''

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(Integer)
    size = Column(Integer)
    asm = Column(String)
    mnem = Column(String)
    oplen = Column(Integer)
    opnds = Column(String)
    optypes = Column(String)
    operandvalues = Column(String)

    def __init__(self, asm):
        if isinstance(asm, dict):
            self.address = asm['address']
            self.size = asm['size']
            self.mnem = asm['mnem']
            self.asm = asm['asm']
            self.oplen = asm['oplen']
            self.opnds = asm['opnds']
            self.optypes = asm['optypes']
            self.operandvalues = asm['operandvalues']

class FuncAsmO(FuncAsm, Base):
    '''
    原始函数汇编信息表
    '''
    __tablename__ = tb_asms_o

class FuncAsmP(FuncAsm, Base):
    '''
    补丁函数汇编信息表
    '''
    __tablename__ = tb_asms_p


if __name__ == "__main__":
    db = DataDb()
    db.create_tb()
