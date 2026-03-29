from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageChops, ImageFilter

from domain.models import CompositionRequest, CompositionResult


class ImageCompositionPipeline:
    def compose(self, image_bytes: bytes, request: CompositionRequest) -> CompositionResult:
        source = Image.open(BytesIO(image_bytes)).convert("RGBA")
        if not self._has_alpha_content(source):
            raise ValueError(
                "Input image must already contain transparency. "
                "Background removal is not implemented yet."
            )

        bbox = source.getbbox()
        if bbox is None:
            raise ValueError("Input image is empty.")

        subject = source.crop(bbox)
        shadow = self._build_shadow(subject, request)

        width = max(subject.width, shadow.width) + request.canvas_padding * 2
        height = max(subject.height, shadow.height) + request.canvas_padding * 2

        canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))

        subject_x = (width - subject.width) // 2
        subject_y = (height - subject.height) // 2

        shadow_x = subject_x
        shadow_y = subject_y + request.shadow_offset_y

        canvas.alpha_composite(shadow, (shadow_x, shadow_y))
        canvas.alpha_composite(subject, (subject_x, subject_y))

        output = BytesIO()
        canvas.convert("RGB").save(output, format="PNG")
        result_bytes = output.getvalue()
        return CompositionResult(image_bytes=result_bytes, width=width, height=height)

    @staticmethod
    def _has_alpha_content(image: Image.Image) -> bool:
        alpha = image.getchannel("A")
        extrema = alpha.getextrema()
        if extrema is None:
            return False
        min_alpha, max_alpha = extrema
        return min_alpha < 255 or max_alpha < 255

    @staticmethod
    def _build_shadow(subject: Image.Image, request: CompositionRequest) -> Image.Image:
        alpha = subject.getchannel("A")
        softened = alpha.filter(ImageFilter.GaussianBlur(radius=request.shadow_blur))
        normalized = ImageChops.multiply(softened, Image.new("L", softened.size, request.shadow_opacity))
        shadow = Image.new("RGBA", subject.size, (0, 0, 0, 0))
        shadow.putalpha(normalized)
        return shadow
