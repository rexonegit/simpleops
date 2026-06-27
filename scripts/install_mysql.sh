#!/bin/bash

# MySQL 8.0 安装和配置脚本
set -e

echo "=== 开始安装 MySQL 8.0 ==="

# 1. 安装 MySQL Yum 仓库
echo "步骤 1: 安装 MySQL Yum 仓库"
yum install -y https://dev.mysql.com/get/mysql84-community-release-el8-2.noarch.rpm

# 2. 查看可用的 MySQL 仓库
echo "步骤 2: 查看可用的 MySQL 仓库"
yum repolist enabled | grep mysql.*-community

# 3. 安装 yum-utils
echo "步骤 3: 安装 yum-utils"
yum -y install yum-utils

# 4. 禁用 MySQL 8.4 LTS 仓库，启用 MySQL 8.0 仓库
echo "步骤 4: 配置 MySQL 仓库"
sudo yum-config-manager --disable mysql-8.4-lts-community
sudo yum-config-manager --enable mysql80-community

# 5. 禁用默认的 MySQL 模块
echo "步骤 5: 禁用默认 MySQL 模块"
sudo yum module disable -y mysql

# 6. 安装 MySQL 服务器
echo "步骤 6: 安装 MySQL 服务器"
sudo yum install -y mysql-community-server

# 7. 启动 MySQL 服务
echo "步骤 7: 启动 MySQL 服务"
systemctl start mysqld
systemctl enable mysqld

# 8. 检查服务状态
echo "步骤 8: 检查 MySQL 服务状态"
systemctl status mysqld

# 9. 获取临时密码
echo "步骤 9: 获取临时 root 密码"
TEMP_PASSWORD=$(sudo grep 'temporary password' /var/log/mysqld.log | awk '{print $NF}')
echo "临时密码: $TEMP_PASSWORD"

# 10. 自动修改 root 密码
echo "步骤 10: 修改 root 密码"
NEW_PASSWORD="MyNewPass4!"

# 使用 expect 工具自动完成密码修改
if command -v expect &> /dev/null; then
    yum install -y expect
fi

expect << EOF
spawn mysql -uroot -p
expect "Enter password:"
send "$TEMP_PASSWORD\r"
expect "mysql>"
send "ALTER USER 'root'@'localhost' IDENTIFIED BY '$NEW_PASSWORD';\r"
expect "mysql>"
send "exit\r"
expect eof
EOF

echo "=== MySQL 安装完成 ==="
echo "Root 密码已设置为: $NEW_PASSWORD"
echo "可以使用以下命令连接: mysql -uroot -p$NEW_PASSWORD"
```

## 如果不想使用 expect，可以使用这个简化版本：

```bash
#!/bin/bash

# MySQL 8.0 安装脚本（手动密码设置）
set -e

echo "=== 开始安装 MySQL 8.0 ==="

# 安装步骤
yum install -y https://dev.mysql.com/get/mysql84-community-release-el8-2.noarch.rpm
yum repolist enabled | grep mysql.*-community
yum -y install yum-utils
sudo yum-config-manager --disable mysql-8.4-lts-community
sudo yum-config-manager --enable mysql80-community
sudo yum module disable -y mysql
sudo yum install -y mysql-community-server

# 启动服务
systemctl start mysqld
systemctl enable mysqld
systemctl status mysqld

# 显示临时密码
echo "=== 请手动执行以下步骤 ==="
echo "1. 获取临时密码: sudo grep 'temporary password' /var/log/mysqld.log"
echo "2. 连接 MySQL: mysql -uroot -p"
echo "3. 修改密码: ALTER USER 'root'@'localhost' IDENTIFIED BY 'MyNewPass4!';"
echo "4. 退出: exit"
