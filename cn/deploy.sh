#!/usr/bin/env bash
# 生成内地站并同步到备案服务器（www.mememo.com.cn）。
#
# 日常改内容的完整流程：
#   1. 改仓库根目录的 index.html / *-zh.html（两站共有的内容）
#   2. git push                  -> mememo.life 自动更新（GitHub Pages）
#   3. bash cn/deploy.sh         -> mememo.com.cn 更新
#
# 只想改内地站专属内容时跳过第 2 步即可。
#
# 服务器地址读自 cn/deploy.env（不进 git）。本仓库是公开的，
# 部署目标不该写在任何人都能浏览的文件里。
set -euo pipefail

cd "$(dirname "$0")/.."

CONF="cn/deploy.env"
if [[ ! -f "$CONF" ]]; then
  echo "缺少 $CONF —— 复制 cn/deploy.env.example 并填入真实值（该文件不进 git）" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$CONF"
: "${SERVER:?cn/deploy.env 里缺少 SERVER}"
: "${WEBROOT:?cn/deploy.env 里缺少 WEBROOT}"

python3 cn/build.py

# --delete：服务器上多出来的文件会被清掉，保证线上与构建产物完全一致。
rsync -avz --delete dist-cn/ "$SERVER:$WEBROOT"

ssh "$SERVER" "nginx -t && systemctl reload nginx"

echo
echo "✅ 已部署 -> https://www.mememo.com.cn"
