#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-03-30T14:49:10+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: getinfo_fromIDA.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-18T14:20:02+08:00
# @Copyright: Copyright by USTC

from idaapi import *
from idc import ARGV
import json
import Queue

'''
修改：将所有函数读取后一次性写入
修改：剔除空节点（block_start == block_end）, 在父节点的子节点中删除该节点
'''

class FunInfo(object):
    '''
    从IDA中获取函数相关信息，写入到json文件
    '''
    def __init__(self, addresslist):
        '''
        初始化：可以从一组地址初始化，也可以从一个地址初始化
        address : 函数内部地址序列
        '''
        if isinstance(addresslist, tuple) or isinstance(addresslist, list):
            self.addresslist = addresslist
            self.address = None
        else:
            self.addresslist = None
            self.address = int(addresslist)

    def _getnodes(self):
        '''
        获取函数节点（基本块）信息
        '''
        nodes = []
        func = get_func(self.address)
        name = Name(func.startEA)
        fc = FlowChart(func)
        init_block = fc[0]
        self.q = Queue.Queue(1000)
        self.s = set()
        self.q.put(init_block)
        self.s.add(init_block.id)
        while not self.q.empty():
            # self.find_child(q.get(), name)
            block = self.q.get()
            node = {}
            if block.startEA == block.endEA:
                self.handle_empty_node_p(nodes, block.id)
                continue
            node['block_id'] = block.id
            node['block_start'] = block.startEA
            node['block_end'] = block.endEA
            node['child'] = []
            for succ_bl in block.succs():
                bl_id = succ_bl.id
                node['child'].append(bl_id)
                if succ_bl.id not in self.s:
                    self.q.put(succ_bl)
                    self.s.add(succ_bl.id)
            nodes.append(node)
        self.s.clear()
        return nodes, name

    def handle_empty_node_p(self, nodes, empty_id):
        '''
        清除节点中的空子节点
        '''
        for n in nodes:
            if empty_id in n['child']:
                n['child'].remove(empty_id)

    def _getasms(self):
        '''
        获取汇编码信息
        '''
        items = []
        func = get_func(self.address)
        for i in FuncItems(func.startEA):
            item = {}
            item['address'] = i
            item['size'] = get_item_size(i)
            item['asm'] = GetDisasm(i)
            item['mnem'] = GetMnem(i)
            item['opnds'] = []
            item['optypes'] = []
            item['operandvalues'] = []
            for x in range(3):
                if GetOpnd(i, x) != '':
                    item['opnds'].append(GetOpnd(i, x))
                    item['optypes'].append(GetOpType(i, x))
                    item['operandvalues'].append(GetOperandValue(i, x))
            items.append(item)
        return items

    def getfunc(self):
        nodes, name = self._getnodes()
        asms = self._getasms()
        funinfo = {'funcname': name, 'nodes': nodes, 'asms': asms}
        return funinfo

    def _handfunc(self):
        '''
        对单个函数进行处理
        '''
        nodes, name = self._getnodes()
        asms = self._getasms()
        funinfo = {'funcname': name, 'nodes': nodes, 'asms': asms}
        with open(self.filename, 'a+') as f:
            json.dump(funinfo, f, sort_keys=True)
            f.write('\n')

    def handle(self, filename):
        '''
        遍历地址，将函数信息写入到json文件
        filename json文件名、|
        '''
        self.filename = filename
        if self.addresslist:
            for address in self.addresslist:
                self.address = address
                self._handfunc()
        if not self.addresslist:
            self._handfunc()

addres = str(ARGV[1])
ouput_filename = str(ARGV[2])

funcs = []

for _addres in addres.split(','):
    finfo = FunInfo(_addres)
    # finfo.handle(ouput_filename)
    funcs.append(finfo.getfunc())

data = {'funcs': funcs}
with open(ouput_filename, 'w') as f:
    json.dump(data, f, sort_keys=True)

idc.Exit(0)
# 在ida界面中执行，可删掉以下注释，并去掉idc.Exit
# if __name__ == '__main__':
#     address = here()
#     finfo = FunInfo(address)
#     finfo.handle('./tmp.json')
