#!/bin/bash

echo "🔧 正在创建虚拟环境 venv ..."
python3 -m venv venv
source venv/bin/activate

echo "⬇️ 安装依赖项 ..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ 安装完成！你现在可以运行爬虫程序了。"

source venv/bin/activate
