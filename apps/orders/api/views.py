from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from gestionPedidos.utils import CustomPagination
from .serializers import (OrderSerializer,
                          UpdateOrderSerializer,
                          ListOrderSerializer,
                          ReportRequestSerializer,
                          ReportGenerationSerializer,
                          ReportDownloadSerializer)
from apps.orders.models import Order
from apps.restaurants.models import Restaurant
from apps.orders.models import ReportRequest
from ..tasks import generate_sales_report
from datetime import timedelta
from django.utils import timezone
from django.http import FileResponse
import os
from apps.orders.api.filters import OrderFilter
from celery.result import AsyncResult


class OrderCreateAPIView(APIView):
    """
    Crea una nueva orden junto con sus items en un solo POST.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Orders"],
        operation_summary="Crear orden con items",
        operation_description="Crea una nueva orden junto con sus items. En el payload se envían los datos de la orden y un array 'items' con los detalles de cada producto.",
        request_body=OrderSerializer,
        responses={201: OrderSerializer()}
    )
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListByRestaurantAPIView(APIView):
    """
    Endpoint para listar órdenes de un restaurante con filtros por fechas.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Orders"],
        operation_summary="Listar órdenes de un restaurante",
        operation_description="Lista las órdenes de un restaurante con opción de filtrar por fechas.",
        manual_parameters=[
            openapi.Parameter(
                'restaurant_id', openapi.IN_PATH,
                description="ID del restaurante",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'start_date', openapi.IN_QUERY,
                description="Fecha de inicio (YYYY-MM-DD)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'end_date', openapi.IN_QUERY,
                description="Fecha de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING
            )
        ]
    )
    def get(self, request, restaurant_id, *args, **kwargs):
        user = request.user

        if user.role == 'ADMIN':
            pass
        elif user.role == 'OWNER':
            if not Restaurant.objects.filter(id=restaurant_id, owner=user).exists():
                return Response(
                    {"error": "You are not the owner of this restaurant"},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif user.role == 'WAITRESS':
            if not user.restaurant or user.restaurant.id != restaurant_id:
                return Response(
                    {"error": "You are not assigned to this restaurant"},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {"error": "You do not have permission to access this resource"},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = Order.objects.filter(restaurant_id=restaurant_id, status=True)

        filterset = OrderFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = filterset.qs

        if 'start_date' not in request.GET and 'end_date' not in request.GET:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])

        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ListOrderSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)


class OrderDetailAPIView(APIView):
    """
    - PUT: Permite actualizar la orden y sus items.
    - DELETE: Realiza una eliminación lógica (cambia status a False).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Orders"],
        operation_summary="Actualizar orden con sus items",
        operation_description=(
            "Actualiza una orden existente. Se permite la actualización si el usuario es ADMIN, "
            "o si es WAITRESS y la orden pertenece a su restaurante, "
            "o si es OWNER y la orden pertenece a un restaurante cuyo owner es él."
        ),
        request_body=OrderSerializer,
        responses={200: OrderSerializer()}
     )
    def put(self, request, restaurant_id, *args, **kwargs):
        try:
            order = Order.objects.get(pk=restaurant_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'WAITRESS':
            if not request.user.restaurant or order.restaurant.id != request.user.restaurant.id:
                return Response(
                    {"detail": "You do not have permission to update orders from a different restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif request.user.role == 'OWNER':
            if order.restaurant.owner != request.user:
                return Response(
                    {"detail": "You do not have permission to update orders for restaurants you do not own."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = UpdateOrderSerializer(order, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Orders"],
        operation_summary="Eliminar orden (lógico)",
        operation_description=(
            "Realiza una eliminación lógica de la orden (cambiando su status a False) y marca como inactivos sus items. "
            "Se permite eliminar si el usuario es ADMIN, o si es WAITRESS y la orden pertenece a su restaurante, "
            "o si es OWNER y la orden pertenece a un restaurante cuyo owner es él."
        ),
        responses={
            204: openapi.Response(description="Order logically deleted."),
            404: openapi.Response(description="Order not found."),
            403: openapi.Response(description="Permission denied.")
        }
    )
    def delete(self, request, restaurant_id, *args, **kwargs):
        try:
            order = Order.objects.get(pk=restaurant_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role == 'WAITRESS':
            if not request.user.restaurant or order.restaurant.id != request.user.restaurant.id:
                return Response(
                    {"detail": "You do not have permission to delete orders from a different restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif request.user.role == 'OWNER':
            if order.restaurant.owner != request.user:
                return Response(
                    {"detail": "You do not have permission to delete orders for restaurants you do not own."},
                    status=status.HTTP_403_FORBIDDEN
                )

        order.status = False
        order.save(update_fields=['status'])
        for item in order.items.all():
            item.status = False
            item.save(update_fields=['status'])
        
        return Response({"detail": "Order deleted."}, status=status.HTTP_204_NO_CONTENT)
    

class ReportGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Report"],
        operation_summary="Generar reporte CSV de ventas",
        operation_description=(
            "Genera un reporte CSV de ventas para todos los restaurantes en un mes y año específicos. "
            "Se deben enviar 'month' y 'year' en el cuerpo de la solicitud."
        ),
        request_body=ReportGenerationSerializer,
        responses={200: openapi.Response(description="Report generation initiated.")}
    )
    def post(self, request, *args, **kwargs):
        serializer = ReportGenerationSerializer(data=request.data)
        if serializer.is_valid():
            month = serializer.validated_data['month']
            year = serializer.validated_data['year']
            
            report_request = ReportRequest.objects.create(
                user=request.user,
                status_report='pending'
            )
            
            task = generate_sales_report.delay(month, year, report_request.id)
            report_request.task_id = task.id
            report_request.save(update_fields=['task_id'])
            
            return Response({
                "task_id": task.id,
                "report_request_id": report_request.id,
                "detail": "Report generation initiated."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Report"],
        operation_summary="Descargar reporte CSV de ventas",
        operation_description=(
            "Descarga el reporte CSV de ventas generado. "
            "En el cuerpo de la solicitud se debe enviar el 'task_id' obtenido en la generación. "
            "Una vez descargado, el archivo se elimina del servidor y se actualiza el registro de ReportRequest."
        ),
        request_body=ReportDownloadSerializer,
        responses={200: openapi.Response(description="CSV file downloaded.")}
    )
    def post(self, request, *args, **kwargs):
        serializer = ReportDownloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        task_id = serializer.validated_data['task_id']

        try:
            report_request = ReportRequest.objects.get(task_id=task_id, user=request.user)
        except ReportRequest.DoesNotExist:
            return Response({"error": "No report request found for this task_id."}, status=status.HTTP_404_NOT_FOUND)
        
        task_result = AsyncResult(task_id)
        if not task_result.ready():
            return Response({"detail": "Report is not ready yet."}, status=status.HTTP_202_ACCEPTED)
        
        result = task_result.result
        file_path = result.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return Response({"error": "Report file not found."}, status=status.HTTP_404_NOT_FOUND)
        
        response = FileResponse(open(file_path, 'rb'), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        
        report_request.status = 'completed'
        report_request.save()
        
        os.remove(file_path)
        return response


class ReportRequestListAPIView(APIView):
    """
    Lista todas las solicitudes de reportes realizadas por el usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Report"],
        operation_summary="Listar solicitudes de reportes",
        operation_description="Obtiene la lista de solicitudes de reportes que ha realizado el usuario autenticado.",
        responses={200: ReportRequestSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        report_requests = ReportRequest.objects.filter(user=request.user).order_by('-created_at')
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(report_requests, request)
        serializer = ReportRequestSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)