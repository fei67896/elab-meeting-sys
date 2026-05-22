# Linly-Talker-Stream (https://github.com/Kedreamix/Linly-Talker-Stream). Copyright [Linly-talker-stream@kedreamix]. Apache-2.0.
# Based on LiveTalking (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking (Apache-2.0).

"""服务器启动和配置"""
import asyncio
from aiohttp import web
import aiohttp_cors

from src.utils.logging import logger
from src.server.state import state
from src.server import routes
from src.server.middleware import auth_middleware
from src.meeting.db import init_db as init_meeting_db


def _warmup_asr():
    """启动时预加载 ASR, 避免首次 /api/transcribe 冷启动卡顿"""
    if state.config is None:
        return
    asr_cfg = getattr(state.config, 'asr', None)
    if asr_cfg is None:
        return
    from src.asr import get_asr_engine
    engine = get_asr_engine(
        asr_type=asr_cfg.type,
        model_size=asr_cfg.model_size,
        device=asr_cfg.device,
    )
    if not engine._initialized:
        engine._load_model()
        engine._initialized = True
    logger.info(f'[ASR] 预热完成: {engine.get_info()}')


async def on_startup(app):
    """启动时初始化会议秘书 SQLite + 预加载 ASR"""
    try:
        await init_meeting_db()
        logger.info('[meeting] SQLite 已初始化')
    except Exception:
        logger.exception('[meeting] SQLite 初始化失败')

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _warmup_asr)
    except Exception:
        logger.exception('[ASR] 预热失败, 首次识别会稍慢')


async def on_shutdown(app):
    """服务器关闭时的清理操作"""
    coros = [pc.close() for pc in state.pcs]
    await asyncio.gather(*coros)
    state.pcs.clear()


def create_app():
    """创建并配置 aiohttp 应用"""
    # 单独设置较大的请求体上限，方便上传音视频
    app = web.Application(
        client_max_size=1024**2*100,
        middlewares=[auth_middleware],
    )
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # ----- Linly-Talker 原协议路径 (不鉴权, 沿用 sessionid) -----
    app.router.add_post("/offer", routes.offer)
    app.router.add_post("/human", routes.human)
    app.router.add_post("/humanaudio", routes.humanaudio)
    app.router.add_post("/asr", routes.asr)
    app.router.add_post('/api/transcribe', routes.transcribe)
    app.router.add_post("/set_audiotype", routes.set_audiotype)
    app.router.add_post("/record", routes.record)
    app.router.add_post("/interrupt_talk", routes.interrupt_talk)
    app.router.add_post("/is_speaking", routes.is_speaking)
    app.router.add_post("/clear_history", routes.clear_history)
    app.router.add_get("/health", routes.health_check)
    app.router.add_get("/download/{filename}", routes.download_record)

    # ----- 认证 (公开) -----
    app.router.add_post('/api/auth/login', routes.login)
    app.router.add_post('/api/auth/login-by-share', routes.login_by_share)
    app.router.add_post('/api/auth/logout', routes.logout)
    app.router.add_get('/api/auth/me', routes.me)

    # ----- 会议秘书 API (需鉴权, 由 middleware 统一拦截) -----
    app.router.add_post('/api/secretary/command', routes.secretary_command)
    app.router.add_get('/api/secretary/mcp-cards', routes.secretary_mcp_cards)
    app.router.add_get('/api/secretary/history', routes.secretary_history)
    app.router.add_get('/api/meetings', routes.list_meetings)
    app.router.add_post('/api/meetings', routes.create_meeting)
    app.router.add_get('/api/meetings/{id}', routes.get_meeting)
    app.router.add_patch('/api/meetings/{id}', routes.update_meeting)
    app.router.add_delete('/api/meetings/{id}', routes.delete_meeting)
    app.router.add_post('/api/meetings/{id}/agendas', routes.add_agenda)
    app.router.add_post('/api/meetings/{id}/participants', routes.add_participant)
    app.router.add_get('/api/meetings/{id}/ics', routes.download_ics)

    # 分享 + 参会
    app.router.add_post('/api/meetings/{id}/share',       routes.create_share)
    app.router.add_get( '/api/meetings/{id}/shares',      routes.list_shares)
    app.router.add_post('/api/meetings/{id}/attendance',  routes.set_attendance)
    app.router.add_get( '/api/meetings/{id}/attendance',  routes.list_attendance)

    # 老系统状态检测历史
    app.router.add_get('/api/legacy/meta', routes.legacy_meta)
    app.router.add_get('/api/legacy/sessions', routes.legacy_sessions)
    app.router.add_get('/api/legacy/sessions/{group_id}/students', routes.legacy_session_students)
    app.router.add_get('/api/legacy/sessions/{group_id}/overview', routes.legacy_meeting_overview)
    app.router.add_get('/api/legacy/sessions/{group_id}/series', routes.legacy_series)

    # 前端静态资源托管
    app.router.add_static('/', path='web')
    
    # 宽松 CORS 方便本地调试和跨域访问
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    
    for route in list(app.router.routes()):
        cors.add(route)
    
    return app


def run_server(app, config):
    """运行服务器"""
    # 兼容新旧配置字段
    use_ssl = getattr(config.app, 'ssl', False)
    if not use_ssl:
        use_ssl = hasattr(config.app, 'ssl_cert') and config.app.ssl_cert and \
                  hasattr(config.app, 'ssl_key') and config.app.ssl_key
    
    protocol = 'https' if use_ssl else 'http'
    listen_host = getattr(config.app, 'listenhost', '0.0.0.0')
    listen_port = config.app.listenport
    
    # 启动信息集中打印，便于排查配置问题
    logger.info('┌─────────────────────────────────────────────┐')
    logger.info('│  🚀 Linly-Talker-Stream 后端服务启动中...   │')
    logger.info('├─────────────────────────────────────────────┤')
    logger.info(f'│  协议: {protocol.upper():<37} │')
    logger.info(f'│  监听地址: {listen_host:<30} │')
    logger.info(f'│  监听端口: {listen_port:<30} │')
    
    if protocol == 'http':
        logger.info('│                                             │')
        logger.info('│  ⚠️  HTTP 模式：浏览器录音仅支持 localhost  │')
        logger.info('│  💡 远程访问需要在配置中启用 ssl: true     │')
    else:
        logger.info(f'│  证书文件: {config.app.ssl_cert:<28} │')
    
    logger.info('└─────────────────────────────────────────────┘')
    
    config.app.protocol = protocol
    
    # 标记可用，供健康检查使用
    state.server_ready = True
    logger.info('✅ 服务已就绪，可以接受连接')
    
    def _run():
        # 独立事件循环，避免与外部线程冲突
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        
        if use_ssl:
            import ssl
            # 仅做服务端 TLS，不做客户端校验
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(config.app.ssl_cert, config.app.ssl_key)
            site = web.TCPSite(runner, listen_host, listen_port, ssl_context=ssl_context)
            logger.info(f'✅ HTTPS 服务已启动: https://{listen_host}:{listen_port}')
        else:
            site = web.TCPSite(runner, listen_host, listen_port)
            logger.info(f'✅ HTTP 服务已启动: http://{listen_host}:{listen_port}')
        
        loop.run_until_complete(site.start())
        loop.run_forever()
    
    _run()
