#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-03T09:44:05+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: block_trace.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-24T09:55:15+08:00
# @Copyright: Copyright by USTC
import networkx as nx
from collections import deque
from simi_block import SimiBlock
from spain import comlog

class Trace(object):
    '''
    轨迹匹配类
    功能：寻找与补丁函数中修改或新增的基本块链可能存在对应关系的基本块链
    难点：在于相同基本块的定义，如何规避同一函数中对个高相似基本块带来混淆匹配
    '''
    def __init__(self, graph_o, graph_p):
        '''
        graph_o: 原始函数cfg图, networkx 类型 节点属性中包含基本块汇编信息
        graph_p: 补丁函数cfg图, networkx 类型 节点属性中包含基本块汇编信息
        '''
        self.graph_o = graph_o
        self.graph_p = graph_p
        self.traces = []
        self.blocks_o = []
        self.blocks_p = []
        self.tags = {}
        self.neighbors_o = None
        self.neighbors_p = None
        self.simi_block = SimiBlock(self.graph_o, self.graph_p)

    def get_trace(self):
        '''
        轨迹算法主体
        '''
        self._match()
        comlog.debug('blocks_p: {}'.format(self.blocks_p))
        comlog.debug('\n\ntags: {}'.format(self.tags))
        traces_p = self.__LinerConnectedComponents(self.blocks_p, 'P')
        for trace_p in traces_p:
            comlog.debug('trace_p: {}'.format(trace_p))
            self.neighbors_p = self.__GetFirstDegreeNeigbors(trace_p)
            comlog.debug('[+]neighbors in patch')
            comlog.debug('\t{}'.format(self.neighbors_p))
            self.neighbors_o = self.__convert_node()
            comlog.debug('[+]neighbors in origin')
            comlog.debug('\t{}'.format(self.neighbors_o))
            self.blocks_o = self.__GetRelevantOriginalBlocks()
            comlog.debug('blocks_o {}'.format(self.blocks_o))
            traces_o = self.__LinerConnectedComponents(self.blocks_o, f_type='O')
            self.traces.append({'trace_p':trace_p, 'traces_o':traces_o})
        return self.traces

    def traces2nodes(self):
        '''
        将轨迹转化为节点列表
        '''
        nodes_o_list = []
        nodes_p_list = []
        for partial_trace in self.traces:
            nodes_o_list.append([node for trace in partial_trace['traces_o'] for node in trace])
            nodes_p_list.append(partial_trace['trace_p'])
        return nodes_o_list, nodes_p_list

    def _match(self):
        '''
        匹配函数
        '''
        tags, scores = self.simi_block.get_simi()
        # print scores
        # import ipdb; ipdb.set_trace()
        # 调试自定义tags
        # tags = {1:1,5:3, 6:4, 8:5, 9:6, 10:7, 11:8, 12:9, 13:10, 14:11}
        self.tags = tags
        self.blocks_p = [n for n in self.graph_p.nodes if n not in tags]

    def __match(self):
        '''
        遍历节点，并匹配对应节点
        '''
        graph_p = self.graph_p
        graph_o = self.graph_o
        nodes_o = list(graph_o.nodes)
        for node in graph_p.nodes:
            FoundMatch = False
            for node_o in nodes_o:
                if self.__node_same(graph_p.nodes[node], graph_o.nodes[node_o]):
                    FoundMatch = True
                    self.tags[node] = node_o
                    break
            if FoundMatch:
                nodes_o.remove(self.tags[node])
            if not FoundMatch:
                self.blocks_p.append(node)

    def __node_same(self, node_p, node_o, cmp=None):
        '''
        cmp: 比较函数 定义节点相等（相似）
             为空，则已节点助记符列表完全相同来判断
        '''
        if not cmp:
            return node_p['mnem_list'] == node_o['mnem_list']
        else:
            return cmp(node_o, node_p)

    def __LinerConnectedComponents(self, nodes, f_type='O'):
        '''
        将存在关系的各个分散节点连接
        '''
        if not nodes:
            comlog.warn('empty blocks')
            return []
        if f_type == 'O':
            graph = self.graph_o
        else:
            graph = self.graph_p
        sub_graph = graph.subgraph(nodes)
        lines = [list(c.node) for c in nx.weakly_connected_component_subgraphs(sub_graph)]
        return lines

    def __convert_node(self):
        '''
        将原补丁函数领域节点对应到原始函数相应节点
        neighors: 节点集
        '''
        return [self.tags[node] for node in self.neighbors_p]


    def __GetFirstDegreeNeigbors(self, line, f_type='P'):
        '''
        获取节点的一阶邻域
        line: 相关节点连接的线
        '''
        neighbors = set()
        if f_type == 'P':
            graph = self.graph_p
        else:
            graph = self.graph_o
        for node in line:
            def _add_to_neighbors(n):
                if n not in line:
                    neighbors.add(n)
            map(_add_to_neighbors, graph.predecessors(node))
            map(_add_to_neighbors, graph.successors(node))
        return list(neighbors)

    def __GetRelevantOriginalBlocks(self):
        '''
        获取原函数对应基本块
        '''
        # 当且仅当与边界点相通
        neighbors = self.neighbors_o
        if len(neighbors) <= 0:
            return []
        graph = self.graph_o
        node_visited = set()
        blocks_o = []
        nodes = self.__GetFirstDegreeNeigbors(neighbors, 'O')
        nodes = [node for node in nodes if node not in self.tags.values()]
        comlog.debug('node to list...')
        comlog.debug(nodes)
        for node in nodes:
            if node not in node_visited:
                degree, blocks = self.__GetBlocksByBounds(node, node_visited)
                if degree == -1:
                    continue
                if degree == len(neighbors):
                    return blocks
                blocks_o.extend(blocks)
        return blocks_o

    def __GetBlocksByBounds(self, start_node, node_visited):
        '''
        根据边界圈定基本块
        '''
        queue = set()
        queue.add(start_node)
        degree_node = set()
        blocks = []
        graph = self.graph_o
        neighbors = self.neighbors_o
        tags = self.tags
        while len(queue) > 0:
            node = queue.pop()
            node_visited.add(node)
            blocks.append(node)
            for predecess in graph.predecessors(node):
                if predecess in neighbors:
                    degree_node.add(predecess)
                if predecess in tags.values() and predecess not in neighbors:
                    comlog.debug('node {} out from {}'.format(node, predecess))
                    return -1, []
                if predecess not in neighbors and predecess not in tags.values():
                    if predecess not in blocks:
                        queue.add(predecess)
            for succ in graph.successors(node):
                if succ in neighbors:
                    degree_node.add(succ)
                if succ in tags.values() and succ not in neighbors:
                    comlog.debug('node {} out from {}'.format(node, succ))
                    return -1, []
                if succ not in neighbors and succ not in tags.values():
                    if succ not in blocks:
                        queue.add(succ)
        return len(degree_node), blocks
