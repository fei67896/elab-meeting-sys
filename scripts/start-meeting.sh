#!/usr/bin/env bash
# ========================================
# 会议秘书前端 - 启动脚本
# 端口 3100, 独立于原 web/ (3000)
# ========================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/web-meeting"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Meeting Secretary - 前端启动 (web-meeting)${NC}"
echo -e "${BLUE}========================================${NC}"

if ! command -v node &>/dev/null; then
  echo -e "${RED}未找到 node, 请先安装 Node.js 18+${NC}"
  exit 1
fi
if ! command -v npm &>/dev/null; then
  echo -e "${RED}未找到 npm${NC}"
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  echo -e "${YELLOW}首次启动, 安装依赖...${NC}"
  npm install --no-fund --no-audit
fi

# 后端地址可通过环境变量覆盖. 默认 3080。
export MEETING_BACKEND="${MEETING_BACKEND:-https://localhost:3080}"
export MEETING_PORT="${MEETING_PORT:-3000}"

echo -e "${GREEN}启动前端开发服务器 :${MEETING_PORT}${NC}"
echo -e "${GREEN}后端地址: ${MEETING_BACKEND}${NC}"
echo ""

exec npm run dev
