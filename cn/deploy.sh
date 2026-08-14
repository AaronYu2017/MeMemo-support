#!/usr/bin/env bash
# 生成内地站并同步到备案服务器（www.mememo.com.cn）。
#
# 日常改内容的完整流程：
#   1. 改仓库根目录的 index.html / *-zh.html（两站共有的内容）
#   2. git push                  -> mememo.life 自动更新（GitHub Pages）
#   3. bash cn/deploy.sh         -> mememo.com.cn 更新
#
# 只想改内地站专属内容时跳过第 2 步即可。
set -euo pipefail

cd "$(dirname "$0")/.."

SERVER="root@47.116.184.7"
WEBROOT="/var/www/mememo/"

python3 cn/build.py

# --delete：服务器上多出来的文件会被清掉，保证线上与构建产物完全一致。
rsync -avz --delete dist-cn/ "$SERVER:$WEBROOT"

ssh "$SERVER" "nginx -t && systemctl reload nginx"

echo
echo "✅ 已部署 -> https://www.mememo.com.cn"
