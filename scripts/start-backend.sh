#!/bin/bash

# ========================================
# Linly-Talker-Stream - 后端启动脚本
# 实时流式数字人对话系统
# ========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 配置文件
CONFIG_FILE="${1:-config/config_talkinggaussian.yaml}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Linly-Talker-Stream - 后端服务启动${NC}"
echo -e "${BLUE}   实时流式数字人对话系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 显示使用说明
show_usage() {
    echo -e "${YELLOW}使用方法:${NC}"
    echo -e "${YELLOW}  $0 [配置文件]${NC}"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo -e "${YELLOW}  $0                                    # 使用默认配置 (wav2lip)${NC}"
    echo -e "${YELLOW}  $0 config/config_wav2lip.yaml        # 使用 wav2lip 配置${NC}"
    echo -e "${YELLOW}  $0 config/config_musetalk.yaml       # 使用 musetalk 配置${NC}"
    echo -e "${YELLOW}  $0 config/config_ernerf.yaml         # 使用 ernerf 配置${NC}"
    echo -e "${YELLOW}  $0 config/config_talkinggaussian.yaml # 使用 talkinggaussian 配置${NC}"
    echo ""
}

# 检查 uv 是否安装
check_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ 错误: 未检测到 uv${NC}"
        echo -e "${YELLOW}请先安装 uv 包管理工具${NC}"
        echo -e "${YELLOW}访问: https://docs.astral.sh/uv/getting-started/installation/${NC}"
        exit 1
    fi
    
    UV_VERSION=$(uv --version)
    echo -e "${GREEN}✓${NC} uv 已安装: $UV_VERSION"
}

# 检查 uv 虚拟环境
setup_uv_env() {
    # 检查 .venv 目录是否存在
    if [ ! -d ".venv" ]; then
        echo -e "${RED}❌ 错误: 虚拟环境 '.venv' 不存在${NC}"
        echo -e "${YELLOW}请先运行: uv venv --python 3.10.19${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} uv 虚拟环境 '.venv' 已找到"

    # 检查 Python 版本
    PYTHON_VERSION=$(uv run python --version)
    echo -e "${GREEN}✓${NC} Python 环境: $PYTHON_VERSION"
}

# 检查配置文件
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}❌ 错误: 配置文件不存在: $CONFIG_FILE${NC}"
        echo ""
        show_usage
        exit 1
    fi

    echo -e "${GREEN}✓${NC} 配置文件: $CONFIG_FILE"
}

# 检查并清理端口
check_and_kill_port() {
    local port=3080
    
    echo -e "${BLUE}🔍 检查端口 $port 是否被占用...${NC}"
    
    # 查找占用端口的进程
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}⚠ 端口 $port 被进程 $pid 占用${NC}"
        
        # 显示进程信息
        local process_info=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
        if [ -n "$process_info" ]; then
            echo -e "${YELLOW}进程信息: $process_info${NC}"
        fi
        
        echo -e "${YELLOW}正在终止占用端口的进程...${NC}"
        kill $pid 2>/dev/null
        
        # 等待进程结束
        sleep 2
        
        # 检查进程是否还存在
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}进程未响应，强制终止...${NC}"
            kill -9 $pid 2>/dev/null
            sleep 1
        fi
        
        # 再次检查端口
        local new_pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$new_pid" ]; then
            echo -e "${RED}❌ 无法清理端口 $port，请手动处理${NC}"
            exit 1
        else
            echo -e "${GREEN}✓${NC} 端口 $port 已清理"
        fi
    else
        echo -e "${GREEN}✓${NC} 端口 $port 可用"
    fi
}

# 启动后端服务
start_backend() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}🎯 启动后端服务...${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    cd "$PROJECT_ROOT"
    
    # 检查并清理端口
    check_and_kill_port

    echo -e "${GREEN}📡 后端服务地址: ${NC}http://localhost:3080"
    echo -e "${YELLOW}💡 按 Ctrl+C 停止服务${NC}"
    echo ""

    uv run python src/server/app.py --config "$CONFIG_FILE"
}

# 主流程
main() {
    check_uv
    setup_uv_env
    check_config
    start_backend
}

# 捕获中断信号
trap 'echo -e "\n${YELLOW}🛑 正在停止后端服务...${NC}"; exit 0' INT TERM

# 执行主流程
main
