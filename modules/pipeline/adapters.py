"""
Pipeline Stage Adapters

Adapters that wrap existing modules as pipeline stages.
"""

from typing import Any, Dict, List, Optional
import logging
import time

from .stage import PipelineStage, StageResult, StageStatus, register_stage
from .context import PipelineContext
from utils.textblock import TextBlock


logger = logging.getLogger(__name__)


class DetectionStage(PipelineStage):
    """
    Text Detection Stage.

    Wraps text detector modules (CTD, YSG, etc.)
    """

    def __init__(self, name: str = "detection", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.detector = None
        self._detector_name = self.config.get('detector', 'default')
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of the detector"""
        if self._initialized:
            return True

        try:
            from modules.textdetector import get_text_detector
            self.detector = get_text_detector(self._detector_name)
            self._initialized = True
            logger.info(f"Initialized detector: {self._detector_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
            return False

    def process(self, blocks: List[TextBlock], image: Any, context: PipelineContext) -> StageResult:
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)

        if not self._ensure_initialized():
            result.status = StageStatus.FAILED
            result.error = "Detector initialization failed"
            return result

        try:
            # Detection works on the image, not existing blocks
            if context.image is None:
                result.status = StageStatus.FAILED
                result.error = "No image in context"
                return result

            # Run detection
            detected_blocks = self.detector.detect(context.image, context.mask)

            result.blocks = detected_blocks
            result.image = context.image
            result.status = StageStatus.SUCCESS
            result.metadata['detector'] = self._detector_name
            result.metadata['block_count'] = len(detected_blocks)

        except Exception as e:
            logger.exception(f"Detection failed: {e}")
            result.status = StageStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result


class OCRStage(PipelineStage):
    """
    OCR Stage.

    Wraps OCR modules (MangaOCR, Paddle, etc.)
    """

    def __init__(self, name: str = "ocr", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.ocr = None
        self._ocr_name = self.config.get('ocr', 'manga_ocr')
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of the OCR"""
        if self._initialized:
            return True

        try:
            from modules.ocr import get_ocr_model
            self.ocr = get_ocr_model(self._ocr_name)
            self._initialized = True
            logger.info(f"Initialized OCR: {self._ocr_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
            return False

    def process(self, blocks: List[TextBlock], image: Any, context: PipelineContext) -> StageResult:
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)

        if not self._ensure_initialized():
            result.status = StageStatus.FAILED
            result.error = "OCR initialization failed"
            return result

        try:
            if not blocks:
                result.blocks = []
                result.status = StageStatus.SUCCESS
                return result

            # Run OCR on each block
            for block in blocks:
                try:
                    text = self.ocr.process_image(block, context.image)
                    block.text = text
                except Exception as e:
                    logger.warning(f"OCR failed for block: {e}")
                    block.text = ""

            result.blocks = blocks
            result.image = image
            result.status = StageStatus.SUCCESS
            result.metadata['ocr'] = self._ocr_name

        except Exception as e:
            logger.exception(f"OCR stage failed: {e}")
            result.status = StageStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result


class TranslationStage(PipelineStage):
    """
    Translation Stage.

    Wraps translator modules (Google, DeepL, etc.)
    """

    def __init__(self, name: str = "translation", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.translator = None
        self._translator_name = self.config.get('translator', 'google')
        self._source_lang = self.config.get('source_lang', 'Auto')
        self._target_lang = self.config.get('target_lang', 'Chinese')
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of the translator"""
        if self._initialized:
            return True

        try:
            from modules.translators import get_translator
            self.translator = get_translator(self._translator_name)
            self._initialized = True
            logger.info(f"Initialized translator: {self._translator_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            return False

    def process(self, blocks: List[TextBlock], image: Any, context: PipelineContext) -> StageResult:
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)

        if not self._ensure_initialized():
            result.status = StageStatus.FAILED
            result.error = "Translator initialization failed"
            return result

        try:
            if not blocks:
                result.blocks = []
                result.status = StageStatus.SUCCESS
                return result

            # Get language from context if set
            source_lang = context.source_lang if context.source_lang != "Auto" else self._source_lang
            target_lang = context.target_lang or self._target_lang

            # Translate each block
            texts_to_translate = [block.text for block in blocks]
            translated_texts = self.translator.translate(
                texts_to_translate,
                source_lang=source_lang,
                target_lang=target_lang,
            )

            for block, translated in zip(blocks, translated_texts):
                block.translated_text = translated

            result.blocks = blocks
            result.image = image
            result.status = StageStatus.SUCCESS
            result.metadata['translator'] = self._translator_name
            result.metadata['source_lang'] = source_lang
            result.metadata['target_lang'] = target_lang

        except Exception as e:
            logger.exception(f"Translation stage failed: {e}")
            result.status = StageStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result


class InpaintingStage(PipelineStage):
    """
    Inpainting Stage.

    Wraps inpainting modules (LaMa, AOT, etc.)
    """

    def __init__(self, name: str = "inpainting", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.inpainter = None
        self._inpainter_name = self.config.get('inpainter', 'lama')
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of the inpainter"""
        if self._initialized:
            return True

        try:
            from modules.inpaint import get_inpainter
            self.inpainter = get_inpainter(self._inpainter_name)
            self._initialized = True
            logger.info(f"Initialized inpainter: {self._inpainter_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize inpainter: {e}")
            return False

    def process(self, blocks: List[TextBlock], image: Any, context: PipelineContext) -> StageResult:
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)

        if not self._ensure_initialized():
            result.status = StageStatus.FAILED
            result.error = "Inpainter initialization failed"
            return result

        if image is None:
            result.blocks = blocks
            result.status = StageStatus.SUCCESS
            return result

        try:
            # Generate combined mask from blocks
            mask = self._generate_mask(blocks, image)

            # Run inpainting
            inpainted_image = self.inpainter.inpaint(image, mask)

            result.blocks = blocks
            result.image = inpainted_image
            result.status = StageStatus.SUCCESS
            result.metadata['inpainter'] = self._inpainter_name

        except Exception as e:
            logger.exception(f"Inpainting stage failed: {e}")
            result.status = StageStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _generate_mask(self, blocks: List[TextBlock], image: Any) -> Any:
        """Generate combined mask from text blocks"""
        import numpy as np

        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        for block in blocks:
            x, y, bw, bh = block.RECT
            mask[y:y+bh, x:x+bw] = 255

        return mask


class RenderingStage(PipelineStage):
    """
    Text Rendering Stage.

    Renders translated text onto the image using TextBlock rendering info.
    """

    def __init__(self, name: str = "rendering", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._font_config = self.config.get('font', {})

    def process(self, blocks: List[TextBlock], image: Any, context: PipelineContext) -> StageResult:
        start_time = time.time()
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)

        if image is None:
            result.status = StageStatus.FAILED
            result.error = "No image to render on"
            return result

        try:
            from utils.textblock import TextBlockRenderer

            renderer = TextBlockRenderer(self._font_config)

            for block in blocks:
                if hasattr(block, 'translated_text') and block.translated_text:
                    image = renderer.render_block(image, block)

            result.blocks = blocks
            result.image = image
            result.status = StageStatus.SUCCESS
            result.metadata['blocks_rendered'] = len(blocks)

        except Exception as e:
            logger.exception(f"Rendering stage failed: {e}")
            result.status = StageStatus.FAILED
            result.error = str(e)

        result.duration_ms = (time.time() - start_time) * 1000
        return result


# Register stage types
register_stage("detection")(DetectionStage)
register_stage("ocr")(OCRStage)
register_stage("translation")(TranslationStage)
register_stage("inpainting")(InpaintingStage)
register_stage("rendering")(RenderingStage)
