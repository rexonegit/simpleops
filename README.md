# 🖥️ 运维工作台 (simpleops)

> 面向多云资源纳管、本地机房 VMware/ProxmoxVE 资产治理、配置管理与自动化运维的一体化工作平台。Django + DRF + MySQL 的后端,Vue 3 + Element Plus + Rspack 的前端。

---

## 🚀 功能概览

运维工作台围绕 **云资源同步 → 资产归属匹配 ** ，将阿里云、本地虚拟化/物理设备、IP 地址库、数据库台账、项目信息及告警登记等分散能力整合到一个统一工作台中。

---

## ☁️ 阿里云资源纳管

通过 **阿里云 API 手动同步** 各类云资源，自动关联 **[项目信息]** 中维护的 **所属项目、环境类型、负责人**，实现资源→项目→责任人的清晰归属链路。

| 序号 | 资源类型             | 说明                                                 |
| :--: | -------------------- | ---------------------------------------------------- |
|  1   | ECS 云服务器         | 实例详情、规格、网络、归属项目                       |
|  2   | OSS 对象存储         | Bucket 列表、地域、存储量、归属、授权详情            |
|  3   | RAM 访问控制         | 用户、角色、权限策略展示                             |
|  4   | 弹性公网 IP          | EIP 详情、绑定资源、带宽                             |
|  5   | 公网 NAT 网关        | SNAT 规则、关联 EIP 展示方便查询服务器对外访问公网IP |
|  6   | RDS 云数据库         | 实例信息、连接地址、归属项目                         |
|  7   | 安全组               | 规则明细、关联主机信息(修改功能未测)                 |
|  8   | Web 应用防火墙 (WAF) | WAF基础信息                                          |
|  9   | SLB 负载均衡         | 监听、后端服务器、VIP                                |
|  10  | NAS 文件存储         | 文件系统、挂载点、容量                               |
|  11  | SLS 日志服务         | Project、Logstore、索引                              |
|  12  | DNS 解析             | 域名、解析记录                                       |

**核心能力：**
- 🔄 资源同步后自动匹配项目信息并展示资源归属明细
- 🏷️ 每条资源均可追溯所属项目、环境类型、负责人
- 📋 统一展示面板，支持搜索按项目、环境、资源类型筛选

---

## 🏭 本地机房资产管理

覆盖虚拟化平台与物理设备，将 **vCenter / ProxmoxVE / 物理机 / 网络设备** 纳入统一台账管理，并整合备份信息。

### VMware 虚拟机

- **路径：** `datacenter/vmwareasset`
- **数据来源：** 同步 vCenter 资源
- **功能：**
  - 自动匹配项目信息（所属项目 / 环境类型 / 负责人）
  - 展示资源明细及归属
  - 🗄️ 可关联 **NetBackup 备份策略** 与 **最近一次备份信息**

### ProxmoxVE 虚拟机

- **路径：** `datacenter/proxmoxasset`
- **数据来源：** 同步 Proxmox Virtual Environment (v9.1.2版本测试通过)
- **功能：**
  - 自动匹配项目信息
  - 展示资源明细及归属
  - 🗄️ 关联 **Proxmox Backup Server (PBS)** 备份信息

### 物理机

- **路径：** `datacenter/projectbaremetal`
- **维护方式：** 手工录入
- **台账内容：**
  - 物理资产基础信息
  - 🔌 **iDRAC /iBMC / 虚拟化地址** 等远程管理连接入口
  - 🔐 管理账号及密码

### 网络设备

- **路径：** `datacenter/projectnetworkdevice`
- **维护方式：** 手工维护
- **内容：** 交换机、路由器、防火墙等网络设备台账

---

## 🗄️ 配置管理 (CMDB)

统一管理数据库实例、内网/公网 IP 地址及子网规划，作为全平台的基础数据源。

### 数据库台账

- **路径：** `cmdb/database`
- **维护方式：** 手工维护
- **内容：** 数据库类型、版本、连接信息、所属项目

### 内网 IP 地址管理

- **路径：** `cmdb/ip_manage/intranet`
- **数据来源：** 从各模块同步 + 手动维护
- **策略：** 🖐️ **手动维护优先** — 手动维护的 IP 地址同步数据时会自动跳过
- **内容：** 所有在用内网 IP、关联资源、使用状态

### 内网 IP 子网管理 (Grid 视图)

- **路径：** `cmdb/ip_manage/IpSubnetGrid`
- **展示形式：** Grid 网格化直观呈现子网使用情况
- **功能：** 子网段划分、已用/可用 IP 可视化、CIDR 管理

### 公网 IP 地址管理

- **路径：** `cmdb/ip_manage/internet`
- **数据来源：** 各模块同步 + 手动维护
- **内容：** 所有在用公网 IP、绑定资源信息

---

## 📋 项目信息管理

- **路径：** `/project`
- **维护内容：**
  - 所属项目
  - 环境类型
```
('prod', '生产环境'),
('test', '测试环境'),
('dev', '开发环境'),
('uat', '用户验收环境'),
('stg', '预生产环境'),
('dr', '灾备环境'),
('other', '其他')
```
  - 负责人
- **核心作用：** 作为 **所有资源 API 同步时的匹配锚点**，确保每一条资源都能准确挂载到对应项目和责任人

---

## ⚙️ 运维管理

- **路径：** `/opsmgmt`
- **特殊告警登记：**
  - 📝 记录特殊告警台账
  - 场景：长期屏蔽的告警、特殊阈值调整记录智能粘贴告警信息识别
  - 便于审计追溯，避免告警策略变更后信息丢失

---

## 🔐 权限控制 (RBAC)

系统具备标准 RBAC（基于角色的访问控制）权限体系，覆盖 **菜单路由 → 页面按钮** 的细粒度管控。

- **路径：** `/permission`
- **核心模型：**
  - 👤 **用户 (User)** — 继承 Django `AbstractUser`，支持多角色挂载
  - 🛡️ **角色 (Role)** — 权限分配的载体，编码全局唯一
  - 🗂️ **菜单路由 (Router)** — 对齐 `vue-router`，支持目录 / 菜单 / 按钮 / 外链四种类型
  - 🔑 **按钮权限 (Permission)** — 与菜单解耦的独立权限标识
- **权限分配：**
  - 角色绑定 **菜单权限**（控制左侧菜单可见性，仅目录/菜单/外链）
  - 角色绑定 **按钮权限**（控制页面内按钮显隐与接口访问）
  - 用户通过角色间接获得菜单与按钮权限
- **菜单管理：** 支持树形结构维护、排序、隐藏、缓存(keepAlive)、固定标签(affix)等 vab 特性

---

## 📝 日志审计

系统内置完整的操作审计能力，所有关键行为均可追溯。

- **路径：** `/monitor/logs`
- **登录日志 (LoginLog)：**
  - 记录用户名、登录 IP、User-Agent、登录成功/失败状态、登录时间
  - 用于登录行为审计与异常登录排查
- **操作日志 (OperationLog)：**
  - 记录操作人、请求 IP、HTTP 方法、请求路径、操作类型
  - 记录状态码、耗时(ms)、请求数据、响应数据
  - 通过中间件自动采集，无需业务代码侵入

---

## 公众号
<p align="center">
  <img src="https://github.com/rexonegit/simpleops/blob/main/example/qrcode.jpg">
</p>


**演示数据效果图展示：**

<table>
<tr>
<td>
<img src="https://github.com/rexonegit/simpleops/blob/main/example/ecs.png">
</td>
<td>
<img src="https://github.com/rexonegit/simpleops/blob/main/example/ip.png">
</td>
</tr>
<tr>
<td>
<img src="https://github.com/rexonegit/simpleops/blob/main/example/pve.png">
</td>
<td>
<img src="https://github.com/rexonegit/simpleops/blob/main/example/vmware.png">
</td>
</tr>
</table>



**仓库地址**

GitHub
[https://github.com/rexonegit/simpleops](url)

Gitee
[https://gitee.com/rexonegit/simpleops](url)

GitCode
[https://gitcode.com/rexonegit/simpleops](url)


**安装数据库和 Python 3.12**

```
scripts 下有 MySQL 8、Python 3.12 脚本(适配 Rocky Linux 8.10)
sh install_mysql.sh
sh install_python3.12.sh
```

**后端启动步骤**

```
新建数据库
CREATE DATABASE django_vue_admin CHARACTER SET utf8mb4;
create USER 'django_vue_admin'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON django_vue_admin.* TO 'django_vue_admin'@'localhost';


sudo yum install mysql-devel gcc -y
cd backend
pip install -r requirements.txt

如果慢使用阿里云源
pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

生成 SECRET_KEY 值
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
注意:生成出来不要带 django-insecure- 前缀,那是 Django 自动生成时给占位密钥打的标记,自己生成的安全密钥不需要这个前缀。


cd backend/django_vue_admin/conf
cp config.example.py config.py
vi config.py
添加 SECRET_KEY 值 数据库名、用户名、密码

建表
cd backend
python manage.py makemigrations
python manage.py migrate

初始化管理员基础菜单
python scripts/init_data.py

启动后端
python manage.py runserver 0.0.0.0:8000
```

**前端启动步骤**

```
前端
前端需要安装 node  
https://nodejs.org/dist/v20.20.2/node-v20.20.2-linux-x64.tar.xz
scripts 下有脚本 sh install_node.sh


启用 pnpm
npm install --global corepack@latest
corepack enable pnpm
pnpm -v

# 安装依赖
pnpm i --registry=http://mirrors.cloud.tencent.com/npm/

如果出现脚本警告
pnpm approve-builds

修改后端配置地址
vi web/src/config/net.config.js
192.168.100.100:8000
192.168.100.100修改为后端服务器IP

# 启动项目
npm run serve:rspack

访问 http://服务器IP地址:8091/

默认管理员
admin
123456


导入菜单
cd backend
python manage.py import_menus --file menu_export.json

备份菜单
cd backend
python manage.py export_menus --output=menu_export-`date '+%F-%H%M%S'`.json
```



配置账号与 Token

```
阿里云/Proxmox/vCenter:从 example 复制并填写
cp backend/aliyun/conf/aliyun.cnf.example backend/aliyun/conf/aliyun.cnf
cp backend/datacenter/conf/proxmox.cnf.example backend/datacenter/conf/proxmox.cnf
cp backend/datacenter/conf/vcenter.cnf.example backend/datacenter/conf/vcenter.cnf
# 然后编辑这三个 .cnf 文件填入真实凭据


阿里云模块配置
backend\aliyun\conf\aliyun.cnf
配置 
access_key = 
access_secret =

支持阿里云多账号，如果只有一个不用的字段 # 注释掉

VMware 和 Proxmox VE
backend\datacenter\conf\vcenter.cnf 配置 vCenter 地址 用户名 密码 需要有只读权限
HOST=
USER=
PASSWORD=

支持多个 vCenter 如果只有一个不用的字段 # 注释掉

backend\datacenter\conf\proxmox.cnf
配置 HOST 地址和 token

# 集群1
# PVE1_HOST=pve2.example.com
# PVE1_USER=cmdb@pve
# PVE1_TOKEN=cmdb@pve!cmdb-token=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
# PVE1_VERIFY_SSL=false

Proxmox VE API 配置说明
# 1. 在 PVE 节点上创建 API 用户
pveum user add cmdb@pve -comment "CMDB Sync User"
# 2. 创建 API Token（更安全，推荐）
pveum user token add cmdb@pve cmdb-token --privsep=0
# 保存输出的 token 值，格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# 3. 创建角色并授权（只读权限）
pveum role add CMDBReader -privs "VM.Audit,Datastore.Audit,Pool.Audit,SDN.Audit,Sys.Audit,VM.GuestAgent.Audit"
记录token 配置到文件中，没加集群就配置多个主机
```



PM2 后台运行

```
【可选】pm2 管理后台前端启动
npm install pm2 -g
cd backend/
pm2 start --name django "python manage.py runserver 0.0.0.0:8000"

cd web/
pm2 start --name vue3 "npm run serve:rspack"
```
