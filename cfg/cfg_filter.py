#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Author: zhangang <zhangang>
# @Date:   2018-04-02T15:53:58+08:00
# @Email:  zhanganguc@gmail.com
# @Filename: cfg_filter.py
# @Last modified by:   zhangang
# @Last modified time: 2018-04-09T16:49:22+08:00
# @Copyright: Copyright by USTC

from post_dom import Dom
import networkx as nx
from operator import itemgetter
from log.mylog import comlog

class CFG(object):
    '''
    3D-CFG筛选
    '''
    def __init__(self, func_graph):
        '''
        @param func_graph 函数图
        '''
        self.func_graph = func_graph.copy()
        self._graph = self.func_graph.copy()
        self.nodesXYZ = {}
        self.is_calculated = False
        self.funcname = self.func_graph.funcname
        self.address = self.func_graph.address

    def calculate(self):
        '''
        一键计算
        init_data[x坐标起始值， 起始节点索引]
        '''
        self.get_dom()
        self._insert_endnode()
        self.get_cyclesnode()
        init_data = {'x':1, 'node_id':0}
        node_visited = [init_data['node_id']]
        self.create_xyz(init_data, node_visited)

    def get_dom(self):
        '''
        获取后支配点
        '''
        graph_dom = Dom(self._graph, start=0)
        graph_dom.run()
        post_dom = graph_dom.get_post_dominators()
        dom_list = graph_dom.get_rdf()
        self.dom_list = dom_list

    def get_cyclesnode(self):
        '''
        获取环路点
        '''
        cycles_node = set()
        for s in nx.strongly_connected_component_subgraphs(self._graph):
            if len(s.node()) > 1:
                for node in s.node():
                    if node not in cycles_node:
                        cycles_node.add(node)
        self.cycles_node = cycles_node

    def _insert_endnode(self):
        '''
        在临时函数图中添加人工节点
        '''
        end_nodes = []
        for node in nx.dfs_preorder_nodes(self._graph):
            if len(list(self._graph.successors(node))) == 0:
                end_nodes.append(node)
        self._graph.add_node('start_node', asms=[],sizes=[],power=0)
        for end_node in end_nodes:
            self._graph.add_edge(end_node,'start_node')

    def _getz(self, node):
        '''
        获取z坐标
        '''
        if node in self.cycles_node:
            return 1
        else:
            return 0

    def _get_branchlsit(self, node_visited, parent_node, start_node):
        '''
        获取分支信息
        @param node_visited 已处理节点
        @param parent_node 分支父节点
        @param start_node 分支开始节点
        @return branchlist 分支节点列表
        @return branchlens 分支长度表
        @return FirstInsLen 分支第一个指令长度
        '''
        # Get the length of Branch
        # print 'call branclist func parent_node %s , start_node %s'%(parent_node,start_node)
        graph = self._graph
        dom_list = self.dom_list
        branchlist = [start_node]
        branchlens = []
        queue = [start_node]
        node_visited = list(node_visited)
        # print node_visited
        node_visited.append(start_node)
        # print node_visited
        s = set()
        while len(queue) > 0:
            node = queue.pop(0)
            s.add(node)
            # print node
            # import pdb; pdb.set_trace()
            for succ in graph.successors(node):
                if succ not in node_visited and succ != dom_list[parent_node] and succ not in s:
                    queue.append(succ)
                    branchlist.append(succ)
                    # print succ
                    branchlens.append(graph.nodes[succ]['power'])
        FirstInsLen = graph.nodes[start_node]['sizes'][0]
        return (branchlist, branchlens, FirstInsLen)


    def create_xyz(self, init_data, node_visited):
        '''
        获取三维坐标
        @param init_data 初始信息 init_data[x坐标起始值， 起始节点索引]
        @param node_visited 已处理节点
        '''
        self.is_calculated = True
        graph = self._graph
        post_dom = self.dom_list
        node = init_data['node_id']
        # print 'node: %s' % node
        dom_is_visited = False
        node_succs = []
        y = 0
        for succ in graph.successors(node):
            y += 1
            if succ not in node_visited:
                node_succs.append(succ)
        succslen = len(node_succs)
        z = self._getz(node)
        # nodeXYZ = {'nodeID':node, 'X':init_data['x'], 'Y':y, 'Z':z}
        # nodesXYZ.append(nodeXYZ)
        self.nodesXYZ[node] = {'X':init_data['x'], 'Y':y, 'Z':z}
        init_data['x'] += 1
        #node_visited.append(node)
        if succslen == 0:
            return
        elif succslen == 1:
            succ_node = node_succs.pop()
            node_visited.append(succ_node)
            init_data['node_id'] = succ_node
            self.create_xyz(init_data, node_visited)
        else:
            branchs = []
            for succ in node_succs:
                if succ != post_dom[node]:
                    branchlist, branchlens, FirstInsLen = self._get_branchlsit(
                                                node_visited, node, succ)
                    branchs.append({'node':succ,'len':len(branchlist),'nodes':branchlist,
                                    'size':sum(branchlens),'sizelist':branchlens,
                                    'FstIns':FirstInsLen})
            branchs = sorted(branchs, key = itemgetter('len','size','FstIns'), reverse=True)
            if post_dom[node] not in node_visited:
                node_visited.append(post_dom[node])
            else:
                dom_is_visited = True
            for branch in branchs:
                succ_node = branch['node']
                if succ_node not in node_visited:
                    node_visited.append(succ_node)
                    init_data['node_id'] = succ_node
                    self.create_xyz(init_data, node_visited)
            if not dom_is_visited:
                init_data['node_id'] = post_dom[node]
                self.create_xyz(init_data, node_visited)


    def get_centroid(self):
        '''
        获取质心
        '''
        if not self.is_calculated:
            self.calculate()
        graph = self._graph
        cx = 0.0
        cy = 0.0
        cz = 0.0
        w = 0.0
        edges_visited = []
        # print graph.edges
        for edge in graph.edges:
            p, q = edge
            if (p, q) in edges_visited or (q, p) in edges_visited:
                continue
            else:
                edges_visited.append((p, q))
            cx += self.nodesXYZ[p]['X'] * graph.nodes[p]['power'] + self.nodesXYZ[q]['X'] * graph.nodes[q]['power']
            cy += self.nodesXYZ[p]['Y'] * graph.nodes[p]['power'] + self.nodesXYZ[q]['Y'] * graph.nodes[q]['power']
            cz += self.nodesXYZ[p]['Z'] * graph.nodes[p]['power'] + self.nodesXYZ[q]['Z'] * graph.nodes[q]['power']
            w += graph.nodes[p]['power'] + graph.nodes[q]['power']
            # print graph.nodes[p]['power'], graph.nodes[q]['power']
            # print w
        # print w
        cx = cx / w
        cy = cy / w
        cz = cz / w
        return (cx, cy, cz, w)

    def same_with(self, cfg_p):
        '''
        比较质心是否相同
        @param cfg_p 另一个cfg对象
        '''
        cx_o, cy_o, cz_o, w_o = self.get_centroid()
        cx_p, cy_p, cz_p, w_p = cfg_p.get_centroid()
        def _cal(x_o, x_p):
            if float(x_o + x_p) == .0:
                return .0
            return abs(x_o - x_p) / float(x_o + x_p)
        CDD = max([_cal(cx_o, cx_p), _cal(cy_o, cy_p), _cal(cz_o, cz_p), _cal(w_o, w_p)])
        # print("funcname: {:>25}\taddress: {:>12}, {:>12} \t CDD: {}".format(self.funcname,
        #                                                 self.address, cfg_p.address, CDD))
        comlog.debug("[+]cfg.same_with funcname:{}".format(self.funcname))
        # if self.funcname == 'print_dot11_mode' and CDD != 0.023400936037441523:
        #     import ipdb; ipdb.set_trace()
        # if CDD == 0:
        if CDD <= 0.01:
            ret = True
        else:
            ret = False
        comlog.debug('same_with :{}'.format(ret))
        return ret
