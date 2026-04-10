import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from features.system.services.images import optimize_image
from PIL import Image


@pytest.mark.unit
def test_optimize_image_converts_to_webp():
    """
    Проверяет, что изображение конвертируется в WebP и уменьшается до max_width.
    """
    # 1. Создаем тестовое изображение (PNG) 2000x1000
    file_io = io.BytesIO()
    image = Image.new("RGB", (2000, 1000), color="red")
    image.save(file_io, format="PNG")
    file_io.seek(0)

    # Имитируем Django ImageField (SimpleUploadedFile)
    uploaded_file = SimpleUploadedFile("test.png", file_io.read(), content_type="image/png")

    # 2. Вызываем оптимизацию (max_width=800)
    optimize_image(uploaded_file, max_width=800)

    # 3. Проверяем результат
    # Имя должно измениться на .webp
    assert uploaded_file.name.endswith(".webp")

    # Открываем результат и проверяем формат и размеры
    result_img = Image.open(uploaded_file)
    assert result_img.format == "WEBP"
    assert result_img.width == 800
    # Высота должна быть 400 (сохранение пропорций 2:1)
    assert result_img.height == 400


@pytest.mark.unit
def test_optimize_image_ignores_none():
    """Проверяет, что функция не падает, если передано None."""
    assert optimize_image(None) is None
