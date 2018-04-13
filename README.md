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
