from PIL import Image


class SegmentationProvider:
    def cutout(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError
