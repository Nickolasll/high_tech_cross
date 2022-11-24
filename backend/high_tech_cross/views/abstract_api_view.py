import json

from abc import ABCMeta

from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils.decorators import method_decorator
from django.http.response import HttpResponse, HttpResponseNotAllowed, Http404
from django.views.decorators.csrf import csrf_exempt

from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.views import APIView


@method_decorator(csrf_exempt, name='dispatch')
class AbstractAPIView(APIView, metaclass=ABCMeta):
    """
    Абстрактный api view для обработки запросов и возврата ответов в формате json.
    """
    serializer: ModelSerializer = None
    validator: Serializer = None

    @staticmethod
    def get_object_or_404(klass, not_found_message: str, *args, **kwargs):
        """
        Wrapper над стандартным шорткатом get_object_or_404 с кастомным сообщением
        :param klass:
        :param not_found_message:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return get_object_or_404(klass, *args, **kwargs)
        except Http404:
            raise NotFound(detail=not_found_message)

    @staticmethod
    def get_list_or_404(klass, not_found_message: str, *args, **kwargs):
        """
        Wrapper над стандартным шорткатом get_list_or_404 с кастомным сообщением
        :param klass:
        :param not_found_message:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return get_list_or_404(klass, *args, **kwargs)
        except Http404:
            raise NotFound(detail=not_found_message)

    def _post(self, *args, **kwargs) -> HttpResponse:
        """
        Здесь должна быть имплементация логики обработки POST запроса.
        По умолчанию, если ничего не реализовано, возвращаем ошибку 405 со списком разрешенных методов запросов.
        :param args:
        :param kwargs:
        :return: HttpResponse в json формате в случае успех
        """
        return HttpResponseNotAllowed(self.http_method_names)

    def post(self, request) -> HttpResponse:
        """
        Стратегия обработки POST запроса.
        Сначала проверяем валидность тела запроса.
        Потом выполняем основной алгоритм.
        :param request:
        :return: HttpResponse в json формате в случае успеха
        """
        if self.validator:
            params = self.validator(data=request.data)
            params.is_valid(raise_exception=True)
            params = params.validated_data
        else:
            params = json.loads(request.data)
        return self._post(**params)
