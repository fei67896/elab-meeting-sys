# eLab Meeting Sys · 智能会议秘书

基于 [Linly-Talker-Stream](https://github.com/Kedreamix/Linly-Talker-Stream) 构建的 **AI 会议秘书 + 实时数字人** 演示系统：语音/文字下达指令，LLM Agent 自动订会、查会、管理议程与参会人，数字人同步播报结果。

> **DEMO · 复旦大学 · 非商用 · 赵一飞信息**  
> 本仓库为教学/演示用途，请勿用于商业场景。

## 功能概览

| 模块 | 说明 |
|------|------|
| **会议秘书 Agent** | 通义千问 function calling，支持创建/查询/取消会议、议程、参会人、指令历史等 |
| **MCP 能力映射** | 工具调用结果映射为预订 / 议程 / 查询 / 历史等结构化展示 |
| **web-meeting** `:3000` | 工作台、会议管理、历史查询（含老系统专注度/情绪/行为） |
| **web-voice** `:3001` | 直播式语音对话界面，数字人居中，外侧贴边展开「已定会议」「专注历史」侧栏 |
| **数字人推流** | WebRTC + Wav2Lip，EdgeTTS 女声播报，口型与字幕近似同步 |
| **语音识别** | 默认服务端 Whisper（`medium`）；Edge 等浏览器走 MediaRecorder + `/api/transcribe` |

### web-voice 界面要点

- 数字人窗口固定居中，左右侧栏向外展开，半透明毛玻璃样式
- 左侧 **已定会议**：滚动列表，一键跳转会议台详情
- 右侧 **专注历史**：最近检测会议的专注度迷你曲线
- 顶栏复旦大学 Logo +「会议秘书」标题
- 页脚 DEMO 标注与开源库致谢

## 系统架构

```text
┌─────────────────┐     ┌─────────────────┐
│  web-meeting    │     │   web-voice     │
│  (Vue3 :3000)   │     │  (Vue3 :3001)   │
└────────┬────────┘     └────────┬────────┘
         │    HTTPS 代理 /api     │
         └──────────┬─────────────┘
                    ▼
         ┌──────────────────────┐
         │  Python 后端 :3080     │
         │  WebRTC / TTS / ASR    │
         │  meeting + legacy API  │
         └──────────┬─────────────┘
                    ▼
              SQLite (meeting.db)
              LLM (DashScope qwen-plus)
```

## 目录结构

```text
elab-meeting-sys/
├── config/config_wav2lip.yaml   # 主配置（端口、Avatar、TTS、ASR、LLM）
├── src/
│   ├── server/                  # aiohttp + WebRTC 服务
│   └── meeting/                 # 会议 CRUD、Agent intent、MCP 注册、Legacy 专注度
├── web-meeting/                 # 会议台前端
├── web-voice/                   # 语音直播前端
├── scripts/                     # 安装与启动脚本
├── models/                      # Wav2Lip 模型权重（Git LFS）
└── data/                        # 数字人素材、会议数据库
```

## 环境要求

- Python 3.10–3.11
- Node.js 18+
- [Git LFS](https://git-lfs.com/)（拉取 `models/wav2lip.pth` 大文件）
- （推荐）NVIDIA GPU + CUDA，用于 Wav2Lip 口型推理与 Whisper ASR
- 阿里云 DashScope API Key（通义千问）
- 自签名 HTTPS 证书（`ssl_certs/`，已入库；也可 `bash scripts/create_ssl_certs.sh` 重新生成）

## 仓库已包含 / 需本机准备

| 内容 | 位置 | 说明 |
|------|------|------|
| Wav2Lip 权重 | `models/wav2lip.pth` | Git LFS，clone 后需 `git lfs pull` |
| 数字人素材 | `data/avatars/` | 已入库，含当前形象 `wav2lip_secretary_weixin` |
| 会议数据库 | `data/meeting.db` | 已入库，含示例会议与历史专注度 |
| HTTPS 证书 | `ssl_certs/` | 已入库 |
| Whisper 权重 | `~/.cache/whisper/` | **不在仓库**，首次启动后端自动下载 `medium`（约 1.4GB） |
| API Key | `.env` | **不在仓库**，从 `.env.example` 复制后填入 |

## 快速开始

### 1. 克隆、拉取 LFS 与 Python 环境

```bash
git clone https://github.com/fei67896/elab-meeting-sys.git
cd elab-meeting-sys

# 拉取大文件（wav2lip.pth 约 205MB；未执行则只有几 KB 的 LFS 指针）
git lfs install
git lfs pull

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e src/avatars/wav2lip/
```

> 完整 Wav2Lip / PyTorch 依赖可参考 [README_zh.md](./README_zh.md) 与 `scripts/setup-env.sh`。RTX 50 系显卡需 PyTorch nightly cu128，勿用 `uv run` 以免版本被回退。

> 若已有另一台机器下载过 Whisper，可复制缓存以跳过下载：`scp -r 旧机:~/.cache/whisper/ ~/.cache/whisper/`

### 2. 配置密钥

```bash
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

或导出环境变量：

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key"
```

### 3. 启动后端（HTTPS :3080）

```bash
source .venv/bin/activate
set -a && source .env && set +a   # 若使用 .env
python src/server/app.py --config config/config_wav2lip.yaml
```

首次启动会下载 Whisper `medium` 到 `~/.cache/whisper/medium.pt`（约 1.4GB），请预留时间与磁盘空间；之后启动直接读缓存，不再重复下载。

### 4. 启动前端

**会议台**（管理、历史、专注度详情）：

```bash
cd web-meeting && npm install && npm run dev
# https://localhost:3000
```

**语音秘书**（直播式语音 + 数字人）：

```bash
cd web-voice && npm install && npm run dev
# https://localhost:3001
```

默认账号见 `src/meeting/db.py` 初始化逻辑（owner 用户 seed，如 `zhaoyifei` / `123456`）。

## 秘书 Agent 示例

只需说出**日期和时间**即可订会，标题可省略（系统自动生成标题与 1 小时时长）：

- 「帮我订明天下午三点的会」
- 「查一下下周有哪些会议」
- 「给当前会议加一条议程：项目进度汇报」
- 「看看最近的指令记录」

API 入口：`POST /api/secretary/command`  
返回含 `intent`、`reply_text`、`mcp_calls`、`mcp_cards`（供前端展示）。

## 主要 API

| 路径 | 说明 |
|------|------|
| `POST /api/secretary/command` | 自然语言指令 → Agent 执行 |
| `GET /api/meetings` | 会议列表 |
| `GET /api/secretary/history` | 指令历史 |
| `POST /api/transcribe` | 服务端语音识别（Whisper） |
| `GET /api/legacy/sessions` | 检测会议列表（专注度等） |
| `GET /api/legacy/sessions/{id}/overview` | 单场专注度/情绪/行为概览 |
| `POST /offer` | WebRTC 建连 |

## 配置说明

编辑 `config/config_wav2lip.yaml`：

| 配置项 | 说明 |
|--------|------|
| `app.listenport` | 后端端口（默认 3080） |
| `model.avatar_id` | 数字人形象 ID（`data/avatars/` 下） |
| `tts.ref_file` | EdgeTTS 音色（默认 `zh-CN-XiaoxiaoNeural` 女声） |
| `asr.mode` | `server`：浏览器录音后送服务端识别 |
| `asr.model_size` | Whisper 模型：`tiny` / `small` / `medium`（推荐 Edge 用 `medium`） |
| `llm.model` | 默认 `qwen-plus` |

## 致谢与开源库

感谢本项目用到的库与上游项目：

- [Linly-Talker-Stream](https://github.com/Kedreamix/Linly-Talker-Stream) · [Linly-Talker](https://github.com/Kedreamix/Linly-Talker) · [LiveTalking](https://github.com/lipku/LiveTalking)
- [Vue 3](https://vuejs.org/) · [Vite](https://vitejs.dev/) · [aiohttp](https://github.com/aio-libs/aiohttp) · [aiortc](https://github.com/aiortc/aiortc)
- [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) · [Whisper](https://github.com/openai/whisper) · [edge-tts](https://github.com/rany2/edge-tts)
- [通义千问 / DashScope](https://help.aliyun.com/zh/model-studio/)

本项目继承上游 Apache-2.0 许可证，详见 [LICENSE](./LICENSE)。
