"""
Whisper ASR 引擎实现
支持 openai-whisper 和 transformers 两种实现
"""

import torch
from typing import Dict, Any

from src.utils.logging import logger
from src.asr.base import BaseASR


class WhisperASR(BaseASR):
    """
    Whisper ASR 引擎
    
    支持两种实现方式：
    1. openai-whisper（推荐）
    2. transformers pipeline（备用）
    """
    
    def __init__(self, config=None, model_size: str = "base", device: str = "auto"):
        """
        初始化 Whisper ASR
        
        Args:
            config: 配置对象
            model_size: 模型大小 ('tiny', 'base', 'small', 'medium', 'large')
            device: auto | cpu | cuda
        """
        super().__init__(config)
        
        self.model_size = model_size
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.model = None
        self.model_type = None
        
        logger.info(f'[Whisper] 模型大小: {model_size}, 设备: {self.device}')
    
    def _load_transformers(self, model_size: str):
        from transformers import pipeline
        model_name = f"openai/whisper-{model_size}"
        logger.info(f'[Whisper] 正在加载 transformers 模型: {model_name}')
        self.model = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=0 if self.device == "cuda" else -1,
        )
        self.model_type = "transformers-whisper"
        self.model_size = model_size
        logger.info('[Whisper] transformers whisper 模型加载成功')

    def _load_model(self):
        """加载 Whisper 模型；无网时自动降级到本地已缓存的 base"""
        candidates = []
        for size in (self.model_size, "base"):
            if size not in candidates:
                candidates.append(size)

        errors = []
        try:
            import whisper
            for size in candidates:
                try:
                    logger.info(f'[Whisper] 正在加载 openai-whisper 模型: {size}')
                    self.model = whisper.load_model(size, device=self.device)
                    self.model_type = "openai-whisper"
                    self.model_size = size
                    logger.info(f'[Whisper] openai-whisper 加载成功 ({size})')
                    return
                except Exception as e:
                    errors.append(f'openai/{size}: {e}')
                    logger.warning(f'[Whisper] openai-whisper {size} 失败: {e}')
        except ImportError as e:
            errors.append(f'openai-whisper 未安装: {e}')

        for size in candidates:
            try:
                self._load_transformers(size)
                return
            except Exception as e:
                errors.append(f'transformers/{size}: {e}')
                logger.warning(f'[Whisper] transformers {size} 失败: {e}')

        raise RuntimeError(
            "Whisper 模型加载失败。请联网下载 tiny/base，或确认 ~/.cache/huggingface 已有模型。\n"
            + "\n".join(errors[-4:])
        )
    
    def _transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        使用 Whisper 识别音频
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            识别结果字典
        """
        if self.model_type == "openai-whisper":
            return self._transcribe_openai(audio_path)
        else:
            return self._transcribe_transformers(audio_path)
    
    def _transcribe_openai(self, audio_path: str) -> Dict[str, Any]:
        """使用 openai-whisper 识别"""
        language = None if self.language == "auto" else self.language
        
        # 会议短句场景: 贪心解码 + 不依赖上文, 显著降低延迟
        result = self.model.transcribe(
            audio_path,
            language=language,
            fp16=(self.device == "cuda"),
            beam_size=1,
            best_of=1,
            temperature=0,
            condition_on_previous_text=False,
            verbose=False,
        )
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", self.language),
            "segments": result.get("segments", [])
        }
    
    def _transcribe_transformers(self, audio_path: str) -> Dict[str, Any]:
        """使用 transformers pipeline 识别"""
        result = self.model(audio_path)
        
        return {
            "text": result["text"].strip(),
            "language": self.language
        }
    
    def get_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        info = super().get_info()
        info.update({
            "model_size": self.model_size,
            "model_type": self.model_type,
            "device": self.device
        })
        return info