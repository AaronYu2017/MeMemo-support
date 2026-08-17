#!/usr/bin/env bash
# 部署 nginx 站点配置到备案服务器。
#
# 与 cn/deploy.sh 刻意分开：内容部署是日常动作，配置部署不是。
# 一份坏配置会让整个站下线，不该搭在每次改文案的顺风车上。
#
# 安全网：先备份线上旧配置 -> 装新的 -> nginx -t -> 不通过立刻回滚。
# 站始终由旧配置提供服务，直到新配置被证明可用为止。
set -euo pipefail

cd "$(dirname "$0")/.."

CONF="cn/deploy.env"
if [[ ! -f "$CONF" ]]; then
  echo "缺少 $CONF —— 复制 cn/deploy.env.example 并填入真实值" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$CONF"
: "${SERVER:?cn/deploy.env 里缺少 SERVER}"
: "${WEBROOT:?cn/deploy.env 里缺少 WEBROOT}"

REMOTE_CONF="/etc/nginx/sites-available/mememo"
STAGED=$(mktemp)
trap 'rm -f "$STAGED"' EXIT

# WEBROOT 带尾斜杠（rsync 需要），nginx 的 root 不要
sed "s|__WEBROOT__|${WEBROOT%/}|" cn/nginx/mememo.conf.template > "$STAGED"

if grep -q "__WEBROOT__" "$STAGED"; then
  echo "模板占位符未被替换，中止" >&2
  exit 1
fi

echo "→ 上传并校验（失败会自动回滚）"
ssh "$SERVER" "cp $REMOTE_CONF $REMOTE_CONF.bak"
scp -q "$STAGED" "$SERVER:$REMOTE_CONF"

if ! ssh "$SERVER" "nginx -t"; then
  echo "✗ 新配置未通过 nginx -t，已回滚，线上未受影响" >&2
  ssh "$SERVER" "mv $REMOTE_CONF.bak $REMOTE_CONF"
  exit 1
fi

ssh "$SERVER" "systemctl reload nginx"
echo
echo "✅ nginx 配置已生效（旧配置留在 $REMOTE_CONF.bak）"
