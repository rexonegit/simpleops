#!/bin/bash

# 自动安装 Node.js 脚本
set -e

# 查找 Node.js 压缩包
node_file=$(find . -maxdepth 1 -name "node-v*-linux-x64.tar.xz" | head -1)

if [[ -z "$node_file" ]]; then
    echo "错误: 未找到 node-v*-linux-x64.tar.xz 文件"
    exit 1
fi

echo "找到 Node.js 文件: $node_file"

# 提取版本号（用于目录名）
node_dir=$(tar -tf "$node_file" | head -1 | cut -f1 -d"/")

# 解压并安装
echo "解压安装中..."
tar -xvJf "$node_file"
sudo mv "$node_dir" /opt/node

# 创建软链接
sudo ln -sf /opt/node/bin/node /usr/local/bin/node
sudo ln -sf /opt/node/bin/npm /usr/local/bin/npm

# 配置环境变量
echo 'export PATH=$PATH:/opt/node/bin' | sudo tee -a /etc/profile > /dev/null

# 立即生效
export PATH=$PATH:/opt/node/bin
echo 'export PATH=$PATH:/opt/node/bin' >> ~/.bashrc
source ~/.bashrc

# 验证安装
echo "安装完成！验证版本："
node -v
npm -v
