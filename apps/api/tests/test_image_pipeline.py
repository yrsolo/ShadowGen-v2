from io import BytesIO

from PIL import Image

from application.services.image_pipeline import ImageCompositionPipeline
from domain.models import CompositionRequest


def build_transparent_sample() -> bytes:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(16, 48):
        for y in range(12, 52):
            image.putpixel((x, y), (220, 40, 40, 255))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pipeline_composes_transparent_subject() -> None:
    pipeline = ImageCompositionPipeline()
    request = CompositionRequest(shadow_blur=10, shadow_opacity=72, canvas_padding=24)

    result = pipeline.compose(build_transparent_sample(), request)

    assert result.width > 64
    assert result.height > 64
    assert result.image_bytes.startswith(b"\x89PNG")


def test_pipeline_rejects_non_transparent_input() -> None:
    image = Image.new("RGB", (32, 32), (255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    pipeline = ImageCompositionPipeline()
    request = CompositionRequest(shadow_blur=10, shadow_opacity=72, canvas_padding=24)

    try:
        pipeline.compose(buffer.getvalue(), request)
    except ValueError as error:
        assert "transparency" in str(error)
    else:
        raise AssertionError("Expected ValueError for non-transparent input")
