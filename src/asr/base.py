"""
ASR 引擎基类
所有 ASR 引擎的统一抽象接口
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import soundfile as sf
import librosa
import numpy as np
from io import BytesIO
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from src.utils.logging import logger

# Whisper 固定 16kHz 单声道, 预先重采样可缩短推理时间
_WHISPER_SR = 16000


def _guess_audio_suffix(audio_bytes: bytes, content_type: Optional[str] = None) -> str:
    """根据 MIME / 文件头推断后缀 (浏览器 MediaRecorder 多为 webm/opus)。"""
    if content_type:
        ct = content_type.lower().split(';')[0].strip()
        mapping = {
            'audio/webm': '.webm',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'audio/x-wav': '.wav',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
            'audio/aac': '.aac',
        }
        if ct in mapping:
            return mapping[ct]

    if len(audio_bytes) >= 4 and audio_bytes[:4] == b'RIFF':
        return '.wav'
    if len(audio_bytes) >= 4 and audio_bytes[:4] == b'OggS':
        return '.ogg'
    if len(audio_bytes) >= 4 and audio_bytes[:4] == b'\x1aE\xdf\xa3':
        return '.webm'
    if len(audio_bytes) >= 8 and audio_bytes[4:8] == b'ftyp':
        return '.m4a'
    return '.webm'


def _write_wav(path: str, data: np.ndarray, samplerate: int = _WHISPER_SR) -> str:
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    if samplerate != _WHISPER_SR:
        data = librosa.resample(data.astype(np.float32), orig_sr=samplerate, target_sr=_WHISPER_SR)
    sf.write(path, data, _WHISPER_SR)
    return path


class BaseASR(ABC):
    """
    所有 ASR 引擎的基类
    
    统一接口：
    - transcribe: 识别音频字节数据
    - set_language: 设置识别语言
    - get_info: 获取引擎信息
    """
    
    def __init__(self, config=None):
        """
        初始化 ASR 引擎
        
        Args:
            config: 配置对象（可选）
        """
        self.config = config
        self.language = "zh"  # 默认中文
        self._initialized = False
        
        logger.info(f'[ASR] 初始化 {self.__class__.__name__}')
    
    @abstractmethod
    def _load_model(self):
        """加载 ASR 模型（子类实现）"""
        pass
    
    @abstractmethod
    def _transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        识别音频文件（子类实现）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict 包含:
                - text: 识别的文本
                - language: 检测到的语言（可选）
                - confidence: 置信度（可选）
        """
        pass
    
    def transcribe(
        self,
        audio_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        识别音频字节数据（统一入口）
        
        Args:
            audio_bytes: 音频文件的字节数据
            content_type: 上传文件的 MIME (可选, 用于 webm 等格式识别)
            
        Returns:
            Dict 包含识别结果
        """
        # 延迟加载模型，避免启动时耗时/占用显存
        if not self._initialized:
            self._load_model()
            self._initialized = True
        
        # 统一转成临时文件，方便不同引擎复用文件接口
        temp_audio_path = None
        raw_path = None
        try:
            temp_audio_path, raw_path = self._save_temp_audio(
                audio_bytes, content_type=content_type
            )
            result = self._transcribe(temp_audio_path)
            
            logger.info(f'[ASR] 识别结果: {result.get("text", "")}')
            return result
            
        finally:
            for path in (temp_audio_path, raw_path):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception as e:
                        logger.warning(f'[ASR] 清理临时文件失败: {e}')
    
    def _save_temp_audio(
        self,
        audio_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        """
        将上传音频转为 16kHz mono wav 临时文件。
        webm/opus 必须先落盘, 不能用 BytesIO (soundfile/librosa 无法识别)。

        Returns:
            (wav_path, raw_path) raw_path 仅当需要后续清理时非 None
        """
        suffix = _guess_audio_suffix(audio_bytes, content_type)
        raw_fd, raw_path = tempfile.mkstemp(suffix=suffix)
        os.close(raw_fd)
        with open(raw_path, 'wb') as f:
            f.write(audio_bytes)

        wav_fd, wav_path = tempfile.mkstemp(suffix='.wav')
        os.close(wav_fd)

        # 1) wav/flac 等可直接用 soundfile 读文件
        if suffix in ('.wav', '.flac', '.ogg'):
            try:
                data, samplerate = sf.read(raw_path)
                _write_wav(wav_path, data, samplerate)
                os.unlink(raw_path)
                logger.debug(f'[ASR] soundfile 解码: {suffix} -> {wav_path}')
                return wav_path, None
            except Exception as e:
                logger.warning(f'[ASR] soundfile 读 {suffix} 失败: {e}')

        # 2) librosa + audioread/ffmpeg 读磁盘文件 (webm 必须走路径)
        try:
            data, _ = librosa.load(raw_path, sr=_WHISPER_SR, mono=True)
            sf.write(wav_path, data, _WHISPER_SR)
            os.unlink(raw_path)
            logger.debug(f'[ASR] librosa 解码: {suffix} -> {wav_path}')
            return wav_path, None
        except Exception as e:
            logger.warning(f'[ASR] librosa 解码 {suffix} 失败: {e}')

        # 3) ffmpeg 兜底 (Edge MediaRecorder webm)
        try:
            proc = subprocess.run(
                [
                    'ffmpeg', '-y', '-loglevel', 'error',
                    '-i', raw_path,
                    '-ar', str(_WHISPER_SR),
                    '-ac', '1',
                    wav_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0 and os.path.getsize(wav_path) > 0:
                os.unlink(raw_path)
                logger.debug(f'[ASR] ffmpeg 解码: {suffix} -> {wav_path}')
                return wav_path, None
            raise RuntimeError(proc.stderr or f'ffmpeg exit {proc.returncode}')
        except FileNotFoundError:
            raise RuntimeError(
                '无法解码 webm 录音: 请安装 ffmpeg (sudo apt install ffmpeg)'
            ) from e
        except Exception as ff_err:
            if os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
            raise RuntimeError(
                f'音频解码失败 ({suffix}, {len(audio_bytes)} bytes): {ff_err}'
            ) from ff_err
    
    def transcribe_text(self, audio_bytes: bytes) -> str:
        """
        简化接口：只返回识别的文本
        
        Args:
            audio_bytes: 音频文件的字节数据
            
        Returns:
            识别的文本字符串
        """
        result = self.transcribe(audio_bytes)
        return result.get("text", "")
    
    def set_language(self, language: str):
        """
        设置识别语言
        
        Args:
            language: 语言代码（如 'zh', 'en', 'auto'）
        """
        self.language = language
        logger.info(f'[ASR] 语言设置为: {language}')
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取 ASR 引擎信息
        
        Returns:
            Dict 包含引擎信息
        """
        return {
            "engine": self.__class__.__name__,
            "language": self.language,
            "initialized": self._initialized
        }


__all__ = ["BaseASR"]
