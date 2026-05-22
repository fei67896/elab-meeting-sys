# eLab Meeting Sys · 智能会议秘书

基于 [Linly-Talker-Stream](https://github.com/Kedreamix/Linly-Talker-Stream) 构建的 **AI 会议秘书 + 实时数字人** 系统：语音/文字下达指令，LLM Agent 自动订会、查会、管理议程与参会人，数字人同步播报结果。

## 功能概览

| 模块 | 说明 |
|------|------|
| **会议秘书 Agent** | 通义千问 function calling，支持创建/查询/取消会议、议程、参会人、指令历史等 |
| **MCP 能力卡片** | 工具调用结果映射到预订 / 议程 / 查询 / 历史等卡片展示 |
| **web-meeting** `:3000` | 工作台、会议管理、历史查询（含老系统专注度/情绪/行为） |
| **web-voice** `:3001` | 直播式语音对话界面，数字人居中，侧栏可展开已定会议与专注度曲线 |
| **数字人推流** | WebRTC + Wav2Lip，EdgeTTS 女声播报，口型与字幕近似同步 |

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
├── config/config_wav2lip.yaml   # 主配置（端口、Avatar、TTS、LLM）
├── src/
│   ├── server/                  # aiohttp + WebRTC 服务
│   └── meeting/                 # 会议 CRUD、Agent intent、MCP 注册、Legacy 专注度
├── web-meeting/                 # 会议台前端
├── web-voice/                   # 语音直播前端
├── scripts/                     # 安装与启动脚本
├── models/                      # 模型权重（需自行下载，不入库）
└── data/                        # 数字人素材、数据库（不入库）
```

## 环境要求

- Python 3.10–3.11
- Node.js 18+
- （推荐）NVIDIA GPU + CUDA，用于 Wav2Lip 口型推理
- 阿里云 DashScope API Key（通义千问）

## 快速开始

### 1. 克隆与 Python 环境

```bash
git clone https://github.com/fei67896/elab-meeting-sys.git
cd elab-meeting-sys

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

> 完整 Wav2Lip 依赖可参考原项目 [README_zh.md](./README_zh.md) 与 `scripts/` 下的安装脚本。

### 2. 配置密钥

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key"
```

或在项目根目录创建 `.env`（已在 `.gitignore` 中忽略）：

```bash
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 启动后端（HTTPS :3080）

```bash
source .venv/bin/activate
python src/server/app.py --config config/config_wav2lip.yaml
```

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

默认账号见 `src/meeting/db.py` 初始化逻辑（owner 用户 seed）。

## 秘书 Agent 示例

只需说出**日期和时间**即可订会，标题可省略：

- 「帮我订明天下午三点的会」
- 「查一下下周有哪些会议」
- 「给当前会议加一条议程：项目进度汇报」
- 「看看最近的指令记录」

API 入口：`POST /api/secretary/command`  
返回含 `intent`、`reply_text`、`mcp_calls`（供前端卡片展示）。

## 主要 API

| 路径 | 说明 |
|------|------|
| `POST /api/secretary/command` | 自然语言指令 → Agent 执行 |
| `GET /api/meetings` | 会议列表 |
| `GET /api/secretary/history` | 指令历史 |
| `GET /api/legacy/sessions` | 检测会议列表（专注度等） |
| `GET /api/legacy/sessions/{id}/overview` | 单场专注度/情绪/行为概览 |
| `POST /offer` | WebRTC 建连 |

## 配置说明

编辑 `config/config_wav2lip.yaml`：

- `app.listenport`：后端端口（默认 3080）
- `model.avatar_id`：数字人形象 ID（`data/avatars/` 下）
- `tts.ref_file`：EdgeTTS 音色（默认 `zh-CN-XiaoxiaoNeural` 女声）
- `llm.model`：默认 `qwen-plus`

## 致谢与许可

- 数字人实时流式框架：[Linly-Talker-Stream](https://github.com/Kedreamix/Linly-Talker-Stream)（Apache-2.0）
- WebRTC 参考：[LiveTalking](https://github.com/lipku/LiveTalking)

本项目继承上游 Apache-2.0 许可证，详见 [LICENSE](./LICENSE)。
