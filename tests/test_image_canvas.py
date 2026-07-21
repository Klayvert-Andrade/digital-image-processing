import numpy as np
from pytestqt.qtbot import QtBot

from imagelab.core.models import ImageDocument, ImageMode
from imagelab.ui.image_canvas import ImageCanvas


def test_image_canvas_supports_fit_and_explicit_zoom(qtbot: QtBot) -> None:
    canvas = ImageCanvas("vazio")
    qtbot.addWidget(canvas)
    canvas.resize(200, 160)
    canvas.show()
    document = ImageDocument(data=np.zeros((100, 100), dtype=np.uint8), mode=ImageMode.GRAYSCALE)
    magnifications: list[int] = []
    canvas.zoom_changed.connect(magnifications.append)

    canvas.set_document(document)
    canvas.zoom_in()
    after_zoom_in = magnifications[-1]
    canvas.zoom_out()
    canvas.set_zoom_percentage(200)
    canvas.fit_to_view()

    assert after_zoom_in > magnifications[0]
    assert 200 in magnifications
    assert magnifications[-1] > 0
    assert canvas.alignment()
