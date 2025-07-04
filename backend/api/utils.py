import io
from typing import Any, Dict, Iterable

from django.db.utils import IntegrityError
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
from .serializers import RecipeMinifiedSerializer, SubscriptionSerializer
from food.models import Favorite, ShoppingCart
from users.models import Subscription


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
    queryset_object = get_object_or_404(queryset, pk=pk)
    if model_class is Favorite:
        field = {'recipe': queryset_object}
        manager = request.user.favorites
        serializer_class = RecipeMinifiedSerializer
    elif model_class is ShoppingCart:
        field = {'recipe': queryset_object}
        manager = request.user.shopping_cart
        serializer_class = RecipeMinifiedSerializer
    elif model_class is Subscription:
        field = {'author': queryset_object}
        manager = request.user.subscriptions
        serializer_class = SubscriptionSerializer
    else:
        raise ValueError('Недопустимый model_class.')
    if request.method == 'DELETE':
        try:
            manager.get(**field).delete()
        except model_class.DoesNotExist:
            raise ValidationError('Does not exist.')
        return Response(status=status.HTTP_204_NO_CONTENT)
    try:
        manager.create(**field)
    except IntegrityError as error:
        error = str(error)
        if 'UNIQUE' in error:
            raise ValidationError('Already exist.')
        if 'author_is_not_follower' in error:
            raise ValidationError('You can not subscribe to yourself.')
        raise ValidationError()
    serializer = serializer_class(
        queryset_object, context={'request': request})
    return Response(serializer.data, status.HTTP_201_CREATED)
