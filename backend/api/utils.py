import io
from typing import Any, Dict, Iterable

from django.db.models import QuerySet
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen.textobject import PDFTextObject
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.request import Request

from . import constants
from .serializers import RecipeMinifiedSerializer


def start_page(file: Canvas) -> tuple[PDFTextObject, list]:
    page = file.beginText(
        constants.HORIZONTAL_INDENT * cm, constants.VERTICAL_INDENT * cm,
    )
    lines = []
    return page, lines


def finish_page(
        page: PDFTextObject, lines: list, file: Canvas,
) -> tuple[PDFTextObject, Canvas]:
    page.textLines(lines)
    file.drawText(page)
    file.showPage()
    return page, file


def get_pdf_in_response(data: Dict[Any, Iterable]) -> FileResponse:
    buffer = io.BytesIO()
    pdfmetrics.registerFont(TTFont('DejaVuSerif', 'fonts/DejaVuSerif.ttf'))
    file = Canvas(
        filename=buffer,
        initialFontName='DejaVuSerif',
        initialFontSize=16,
        initialLeading=1 * cm,
    )
    page, lines = start_page(file)
    for key, value in data.items():
        line = f'- {key}: {" ".join(map(str, value))}'
        for row_start in range(0, len(line), constants.MAX_COLUMN_COUNT):
            lines.append(
                line[row_start:row_start + constants.MAX_COLUMN_COUNT]
            )
            if len(lines) >= constants.MAX_ROW_COUNT:
                page, file = finish_page(page, lines, file)
                page, lines = start_page(file)
    page, file = finish_page(page, lines, file)
    file.save()
    buffer.seek(0)
    return FileResponse(
        buffer, as_attachment=True, filename='shopping_cart.pdf',
    )


def create_delete_object(
        model_class: type, request: Request, queryset: QuerySet, pk: int,
) -> Response:
    recipe = get_object_or_404(queryset, pk=pk)
    if request.method == 'DELETE':
        was_deleted, _ = model_class.objects.filter(
            recipe=recipe, user=request.user,
        ).delete()
        if not was_deleted:
            raise ValidationError('Рецепт не был добавлен.')
        return Response(status=status.HTTP_204_NO_CONTENT)
    _, was_created = model_class.objects.get_or_create(
        recipe=recipe, user=request.user,
    )
    if not was_created:
        raise ValidationError('Рецепт уже добавлен.')
    serializer = RecipeMinifiedSerializer(recipe, context={'request': request})
    return Response(serializer.data, status.HTTP_201_CREATED)
