# spain

**必备**
linux 环境下
ida pro
bindiff

需要将软连接 differ -> /opt/zynamics/BinDiff/bin/differ
在项目下链接differ命令
语义分析需安装
angr模块

**注意**
在运行时需要退出ida, 不然回报`raise BinException('call idc wrong!')`错误

**当前目录介绍**
- binfile目录负责处理二进制文件，生成bindiff结果数据库，函数信息数据库
- block目录 负责补丁基本块定位, 通过基本块串联
- cfg目录 负责补丁函数定位，通过3d-cfg筛选
- seman目录 负责语义分析
- log目录 提供日志接口
- test目录 单元测试

2018年04月11日，今日解决后支配点bug，测试ysg相似度代码
2018年04月13日09:32:02，以上以完成

现在修复基本块匹配bug

现阶段的关键问题是基本块的匹配

basicBlock: edges prime product
basicBlock: hash matching
basicBlock: prime matching
basicBlock: call reference matching
basicBlock: string references matching
basicBlock: edges MD index (top down)
basicBlock: MD index matching (top down)
basicBlock: edges MD index (bottom up)
basicBlock: MD index matching (bottom up)


首先基于这样一个事实，所研究的函数中相似的块占比大
每个函数都有一个起始节点，起始点可能相似，也可能不同（即发生变化）
往下走 可能存在多个分支，**问题1**，将分支对应起来，再在分支里比较
    在分支里面，理论上可以在分分支

```python
#dtls1_process_heartbeat
#原函数
{0: {1: {}, 2: {}}, 1: {2: {}}, 2: {3: {}, 5: {}}, 3: {9: {}, 4: {}}, 4: {}, 5: {8: {}, 6: {}}, 6: {8: {}, 7: {}}, 7: {8: {}}, 8: {4: {}}, 9: {10: {}, 4: {}}, 10: {11: {}, 4: {}}, 11: {4: {}}}

#补丁函数
{0: {1: {}, 2: {}}, 1: {2: {}}, 2: {3: {}, 6: {}}, 3: {4: {}, 6: {}}, 4: {5: {}, 7: {}}, 5: {12: {}, 6: {}}, 6: {}, 7: {8: {}, 6: {}}, 8: {9: {}, 11: {}}, 9: {10: {}, 11: {}}, 10: {11: {}}, 11: {6: {}}, 12: {13: {}, 6: {}}, 13: {14: {}, 6: {}}, 14: {6: {}}}
```
0 和 0`是不匹配的
    他们下面有两个分支。
