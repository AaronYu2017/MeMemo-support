#!/usr/bin/env bash
# 部署 App Store Server Notifications 接收端到备案服务器。
#
# 与 cn/deploy.sh（网站内容）和 cn/deploy-nginx.sh（站点配置）刻意分开：
# 这是第三种东西，有自己的失败模式，不该搭在改文案的顺风车上。
#
# 安全网与 deploy-nginx.sh 同一套：先把服务跑起来并自检通过，**再**装 nginx 片段；
# nginx -t 不过立刻回滚。网站在整个过程中一秒都不受影响。
#
# 幂等：重复跑是安全的，可以当"更新代码后重新部署"用。
set -euo pipefail

cd "$(dirname "$0")/../.."          # 仓库根

SERVER_CONF="cn/deploy.env"
ASN_CONF="cn/asn/asn.env"
for f in "$SERVER_CONF" "$ASN_CONF"; do
  [[ -f "$f" ]] || { echo "缺少 $f —— 复制同目录的 .example 并填真实值（不进 git）" >&2; exit 1; }
done
# shellcheck source=/dev/null
source "$SERVER_CONF"
: "${SERVER:?cn/deploy.env 里缺少 SERVER}"

ASN_PATH_TOKEN=$(grep -E '^ASN_PATH_TOKEN=' "$ASN_CONF" | cut -d= -f2- | tr -d '"'"'"' ')
[[ -n "$ASN_PATH_TOKEN" ]] || { echo "$ASN_CONF 里 ASN_PATH_TOKEN 是空的（生成：openssl rand -hex 16）" >&2; exit 1; }
[[ "$ASN_PATH_TOKEN" =~ ^[A-Za-z0-9_-]{16,}$ ]] || { echo "ASN_PATH_TOKEN 必须是 >=16 位的 URL 安全字符" >&2; exit 1; }

APP_DIR=/opt/mememo-asn
PY_MIRROR=https://mirrors.aliyun.com/pypi/simple/   # 系统默认的 mirrors.cloud.aliyuncs.com 证书 SAN 不匹配，装不了

echo "→ 1/7 建服务账号与目录"
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
# python3-venv 不是 Ubuntu 22.04 的默认件。注意 \`import venv\` 成功**不代表**能建 venv：
# 模块在，缺的是 ensurepip。探测必须真的建一个，不能只 import。
python3 -m venv /tmp/.venvprobe >/dev/null 2>&1 || {
  export DEBIAN_FRONTEND=noninteractive
  apt-get install -y -q python3.10-venv >/dev/null
}
rm -rf /tmp/.venvprobe
id -u mememo-asn >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin mememo-asn
mkdir -p $APP_DIR/certs
REMOTE

echo "→ 2/7 同步代码"
# venv/ 和 certs/ 只存在于服务器上，本地没有 —— 不排除的话 --delete 会把它们删掉。
rsync -az --delete --exclude 'venv/' --exclude 'certs/' --exclude '__pycache__/' --exclude 'asn.env' \
  cn/asn/ "$SERVER:$APP_DIR/"

echo "→ 3/7 装依赖（venv）"
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
# 判据是 pip 在不在，不是目录在不在 —— 半成品 venv 目录也是存在的，
# 上一次因为缺 ensurepip 失败就留下过一个。
[[ -x $APP_DIR/venv/bin/pip ]] || { rm -rf $APP_DIR/venv; python3 -m venv $APP_DIR/venv; }
$APP_DIR/venv/bin/pip install -q --upgrade pip -i $PY_MIRROR
$APP_DIR/venv/bin/pip install -q -r $APP_DIR/requirements.txt -i $PY_MIRROR
REMOTE

echo "→ 4/7 取 Apple 根证书"
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
mkdir -p $APP_DIR/certs && cd $APP_DIR/certs
if [[ ! -s AppleRootCA-G3.cer ]]; then
  curl -fsS -o AppleRootCA-G3.cer https://www.apple.com/certificateauthority/AppleRootCA-G3.cer
fi
# 验一下确实是那张根证书，而不是一页 HTML 错误页
openssl x509 -inform DER -in AppleRootCA-G3.cer -noout -subject | grep -q "Apple Root CA - G3"
REMOTE

# 本地 asn.env 是唯一真源，每次部署都覆盖服务器上的 /etc/mememo-asn.env。
# 所以本地这份要是空的，会**静默**把服务器上填好的值清掉，提醒从此不再发出，
# 而且外观上一切正常。宁可在这里吵一声。
if ! grep -qE '^ASN_BARK_KEY=.+' "$ASN_CONF"; then
  echo "⚠️  $ASN_CONF 里 ASN_BARK_KEY 是空的 —— 部署后不会推送任何提醒（只落盘）。" >&2
  if ssh "$SERVER" "grep -qE '^ASN_BARK_KEY=.+' /etc/mememo-asn.env" 2>/dev/null; then
    echo "🔴 服务器上那份**已经填了**，继续部署会把它清掉。" >&2
    echo "   先把 key 补进 $ASN_CONF 再重跑；确实要清空就 ALLOW_EMPTY_BARK=1 再跑。" >&2
    [[ "${ALLOW_EMPTY_BARK:-}" == "1" ]] || exit 1
  fi
fi

echo "→ 5/7 装配置与 systemd 单元"
scp -q "$ASN_CONF" "$SERVER:/etc/mememo-asn.env"
scp -q cn/asn/systemd/*.service cn/asn/systemd/*.timer "$SERVER:/etc/systemd/system/"
ssh "$SERVER" bash -s <<'REMOTE'
set -euo pipefail
chown root:mememo-asn /etc/mememo-asn.env && chmod 0640 /etc/mememo-asn.env
chown -R root:root /opt/mememo-asn && chmod -R go-w /opt/mememo-asn
systemctl daemon-reload
systemctl enable --now mememo-asn.service >/dev/null
systemctl restart mememo-asn.service
systemctl enable --now mememo-asn-drain.timer >/dev/null

# 心跳要 In-App Purchase API 密钥（独立于 App Store Connect API 密钥）。
# 三样齐了才启用 timer —— 少一样就跑不起来，与其让 systemd 每周失败一次，
# 不如干脆不启用并说清楚缺什么。
KEY_PATH=$(grep -E '^ASN_IAP_KEY_PATH=' /etc/mememo-asn.env | cut -d= -f2-)
if grep -qE '^ASN_IAP_KEY_ID=.+' /etc/mememo-asn.env \
   && grep -qE '^ASN_IAP_ISSUER_ID=.+' /etc/mememo-asn.env \
   && [[ -s "${KEY_PATH:-/nonexistent}" ]]; then
  chown root:mememo-asn "$KEY_PATH" && chmod 0640 "$KEY_PATH"
  systemctl enable --now mememo-asn-heartbeat.timer >/dev/null
  echo "   心跳已启用（每周一 10:00）"
else
  systemctl disable --now mememo-asn-heartbeat.timer >/dev/null 2>&1 || true
  echo "   心跳未启用：还缺 ASN_IAP_KEY_ID / ASN_IAP_ISSUER_ID / 密钥文件 其中之一"
fi
REMOTE

echo "→ 6/7 自检（服务是否真的起来了）"
ssh "$SERVER" bash -s <<REMOTE
set -euo pipefail
sleep 2
systemctl is-active --quiet mememo-asn.service || { journalctl -u mememo-asn -n 30 --no-pager; exit 1; }
$APP_DIR/venv/bin/python -c "
import os,sys; sys.path.insert(0,'$APP_DIR'); os.chdir('$APP_DIR')
os.environ['ASN_ENV_FILE']='/etc/mememo-asn.env'
sys.argv=['asn.py','selftest']; import asn; raise SystemExit(asn.main())"
# 存储层回归测试（去重 / 保留期 / 待推送队列）。用临时目录，不碰真实数据。
$APP_DIR/venv/bin/python $APP_DIR/test_asn.py | tail -3
# 直接打回环端口：错的路径必须是 404，证明 token 校验在生效
code=\$(curl -s -o /dev/null -w '%{http_code}' -X POST -d '{}' http://127.0.0.1:8787/asn/wrong-token/prod)
[[ "\$code" == "404" ]] || { echo "错路径应回 404，实际 \$code" >&2; exit 1; }
echo "   服务在跑，token 校验生效"
REMOTE

echo "→ 7/7 装 nginx 片段（失败自动回滚）"
SNIPPET=/etc/nginx/snippets/mememo-asn.conf
STAGED=$(mktemp); trap 'rm -f "$STAGED"' EXIT
sed "s|__ASN_TOKEN__|${ASN_PATH_TOKEN}|" cn/asn/nginx/asn.conf.template > "$STAGED"
grep -q "__ASN_TOKEN__" "$STAGED" && { echo "占位符未替换，中止" >&2; exit 1; }

ssh "$SERVER" "mkdir -p /etc/nginx/snippets && cp $SNIPPET $SNIPPET.bak 2>/dev/null || true"
scp -q "$STAGED" "$SERVER:$SNIPPET"
if ! ssh "$SERVER" "nginx -t"; then
  echo "✗ nginx -t 未通过，回滚，线上未受影响" >&2
  ssh "$SERVER" "if [[ -f $SNIPPET.bak ]]; then mv $SNIPPET.bak $SNIPPET; else rm -f $SNIPPET; fi"
  exit 1
fi
ssh "$SERVER" "systemctl reload nginx"

# 光有片段没用 —— 站点配置得真的 include 它。第一次部署时就栽在这：
# 片段装好了、nginx -t 也过了（没被引用的片段天然合法），端点却全是 404。
if ! ssh "$SERVER" "grep -q 'mememo-asn' /etc/nginx/sites-available/mememo"; then
  echo "✗ 站点配置没有 include 这个片段，端点不会生效。" >&2
  echo "  先跑 bash cn/deploy-nginx.sh 把带 include 的站点配置推上去，再重跑本脚本。" >&2
  exit 1
fi

echo "→ 端到端检查（走公网 HTTPS，不是本地回环）"
BASE="https://www.mememo.com.cn/asn/${ASN_PATH_TOKEN}"
# ⚠️ 下面这个函数里的 ${what} / ${got} **必须带花括号**，别"简化"掉。
# macOS 自带的 bash 3.2 在 UTF-8 locale 下会把紧跟其后的多字节字符（这里是全角括号）
# 的第一个字节吞进变量名，set -u 下当场报 unbound variable。2026-08-28 真炸过一次。
# test_asn.py 里有一条自动检查守着这个 —— 开发机 locale 是 C，人工是测不出来的。
check() {  # 期望码 描述 curl参数...
  local want=$1 what=$2; shift 2
  local got; got=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$@")
  if [[ "$got" != "$want" ]]; then echo "   ✗ ${what}：期望 ${want}，实际 $got" >&2; return 1; fi
  echo "   ✓ ${what}（${got}）"
}
fail=0
# 垃圾签名必须被拒 —— 这条要是过了，说明验签根本没在跑
check 400 "垃圾签名被验签拒绝"  -X POST -H 'Content-Type: application/json' \
      -d '{"signedPayload":"garbage.garbage.garbage"}' "$BASE/prod" || fail=1
check 400 "sandbox 路径通"      -X POST -H 'Content-Type: application/json' \
      -d '{"signedPayload":"a.b.c"}' "$BASE/sandbox" || fail=1
check 403 "GET 被 nginx 挡掉"   "$BASE/prod" || fail=1
check 404 "错 token 不暴露端点"  -X POST -d '{}' \
      "https://www.mememo.com.cn/asn/00000000000000000000000000000000/prod" || fail=1
check 200 "网站首页未受影响"     "https://www.mememo.com.cn/" || fail=1
[[ $fail -eq 0 ]] || { echo "✗ 端到端检查未通过，端点可能不工作" >&2; exit 1; }

cat <<DONE

✅ 部署完成。把下面两个 URL 填进 App Store Connect
   （App -> App 信息 -> App Store Server Notifications，版本选 **Version 2**）：

   Production Server URL:  https://www.mememo.com.cn/asn/${ASN_PATH_TOKEN}/prod
   Sandbox Server URL:     https://www.mememo.com.cn/asn/${ASN_PATH_TOKEN}/sandbox

   排查：ssh $SERVER 'journalctl -u mememo-asn -f'
   流水：ssh $SERVER 'cd /opt/mememo-asn && sudo -u mememo-asn venv/bin/python asn.py tail 20'
DONE
