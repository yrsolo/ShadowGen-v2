from dataclasses import dataclass


@dataclass(slots=True)
class CompositionRequest:
    shadow_blur: int
    shadow_opacity: int
    canvas_padding: int
    shadow_offset_y: int = 18


@dataclass(slots=True)
class CompositionResult:
    image_bytes: bytes
    width: int
    height: int
