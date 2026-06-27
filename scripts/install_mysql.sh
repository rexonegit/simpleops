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
