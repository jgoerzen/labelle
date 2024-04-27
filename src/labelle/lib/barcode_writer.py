# === LICENSE STATEMENT ===
# Copyright (c) 2011 Sebastian J. Bronner <waschtl@sbronner.com>
#
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.
# === END LICENSE STATEMENT ===

from typing import List, Optional, Tuple

from barcode.writer import BaseWriter
from PIL import Image, ImageDraw


def _mm2px(mm: float, dpi: float = 25.4) -> float:
    return (mm * dpi) / 25.4


def _calculate_size(
    *,
    modules_per_line: int,
    number_of_lines: int,
    quiet_zone: float,
    module_width: float,
    module_height: float,
    vertical_margin: float,
    dpi: float = 25.4,
) -> Tuple[int, int]:
    width = 2 * quiet_zone + modules_per_line * module_width
    height = vertical_margin * 2 + module_height * number_of_lines
    return int(_mm2px(width, dpi)), int(_mm2px(height, dpi))


class BarcodeImageWriter(BaseWriter):
    _draw: Optional[ImageDraw.ImageDraw]
    _image: Optional[Image.Image]

    def __init__(self) -> None:
        super().__init__(None, None, None, None)
        self.format = "PNG"
        self.dpi = 25.4
        self._image = None
        self._draw = None
        self.vertical_margin = 0

    def render(self, code: List[str]) -> Image.Image:
        """Render the barcode.

        Uses whichever inheriting writer is provided via the registered callbacks.

        :parameters:
            code : List
                List of strings matching the writer spec
                (only contain 0 or 1).
        """
        width, height = _calculate_size(
            modules_per_line=len(code[0]),
            number_of_lines=len(code),
            dpi=self.dpi,
            quiet_zone=self.quiet_zone,
            module_width=self.module_width,
            module_height=self.module_height,
            vertical_margin=self.vertical_margin,
        )
        self._image = Image.new("1", (width, height), self.background)
        self._draw = ImageDraw.Draw(self._image)

        ypos = self.vertical_margin
        for cc, line in enumerate(code):
            # Pack line to list give better gfx result, otherwise in can
            # result in aliasing gaps
            # '11010111' -> [2, -1, 1, -1, 3]
            line += " "
            c = 1
            mlist = []
            for i in range(0, len(line) - 1):
                if line[i] == line[i + 1]:
                    c += 1
                else:
                    if line[i] == "1":
                        mlist.append(c)
                    else:
                        mlist.append(-c)
                    c = 1
            # Left quiet zone is x startposition
            xpos = self.quiet_zone
            for mod in mlist:
                if mod < 1:
                    color = self.background
                else:
                    color = self.foreground
                # remove painting for background colored tiles?
                _paint_module(
                    xpos=xpos,
                    ypos=ypos,
                    width=self.module_width * abs(mod),
                    color=color,
                    dpi=self.dpi,
                    module_height=self.module_height,
                    draw=self._draw,
                )
                xpos += self.module_width * abs(mod)
            # Add right quiet zone to every line, except last line,
            # quiet zone already provided with background,
            # should it be removed complety?
            if (cc + 1) != len(code):
                _paint_module(
                    xpos=xpos,
                    ypos=ypos,
                    width=self.quiet_zone,
                    color=self.background,
                    dpi=self.dpi,
                    module_height=self.module_height,
                    draw=self._draw,
                )
            ypos += self.module_height
        return _finish(self._image)


def _paint_module(
    *,
    xpos: float,
    ypos: float,
    width: float,
    color: str,
    dpi: float,
    module_height: float,
    draw: ImageDraw.ImageDraw,
) -> None:
    size = (
        (_mm2px(xpos, dpi), _mm2px(ypos, dpi)),
        (
            _mm2px(xpos + width, dpi),
            _mm2px(ypos + module_height, dpi),
        ),
    )
    draw.rectangle(size, outline=color, fill=color)


def _finish(image: Image.Image) -> Image.Image:
    # although Image mode set to "1", draw function writes white as 255
    return image.point(lambda x: 1 if x > 0 else 0, mode="1")
