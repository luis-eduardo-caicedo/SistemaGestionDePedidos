import os
import uuid
import csv
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from .serializers import (UserRegistrationSerializer,
                          PasswordChangeSerializer,
                          UserSerializer,
                          ClientSerializer)
from drf_yasg import openapi
from django.conf import settings
from apps.users.models import User, Client
from apps.users.api.filters import UserFilter, ClientFilter
from gestionPedidos.utils import CustomPagination
from .serializers import BulkClientUploadSerializer
from apps.users.tasks import process_bulk_clients
from celery.result import AsyncResult



class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Endpoint para obtener el token de acceso"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Endpoint para refrescar el token"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserRegistrationView(APIView):
    permission_classes = [IsAuthenticated] 
    
    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Registro de usuario",
        operation_description="Endpoint para registrar nuevos usuarios",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Usuario registrado exitosamente",
                examples={"application/json": {"detail": "User successfully registered"}}
            ),
            400: openapi.Response(
                description="Error en la validación",
                examples={"application/json": {"username": ["Este campo es requerido"], "email": ["Ingrese un email válido"]}}
            )
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User successfully registered"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Cambiar la contraseña del usuario",
        operation_description="Endpoint para cambiar la contraseña",
        request_body=PasswordChangeSerializer,
        responses={
            201: openapi.Response(
                description="Password successfully updated.",
                examples={"application/json": {"detail": "User successfully registered"}}
            ),
            400: openapi.Response(
                description="Error en la validación",
                examples={"application/json": {"username": ["Este campo es requerido"], "email": ["Ingrese un email válido"]}}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"detail": "Password successfully updated."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListAPIView(APIView):
    """
    Lista todos los usuarios y permite filtrar por role, username, first_name y last_name usando django-filters.
    Se aplica paginación manual; por defecto se muestran 10 elementos, pero se puede modificar con el query param 'limit'.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Listar usuarios con filtros",
        operation_description=(
            "Obtiene la lista de usuarios. Se pueden aplicar filtros utilizando los siguientes parámetros de query:\n"
            "- role (por ejemplo, ADMIN, WAITRESS, OWNER)\n"
            "- username (contiene)\n"
            "- first_name (contiene)\n"
            "- last_name (contiene)\n"
            "También se puede paginar usando el query param 'limit' (por defecto 10 elementos por página)."
        ),
        manual_parameters=[
            openapi.Parameter(
                'role', openapi.IN_QUERY,
                description="Filtra por rol (por ejemplo, ADMIN, CUSTOMER, WAITRESS, OWNER)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'username', openapi.IN_QUERY,
                description="Filtra por username (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'first_name', openapi.IN_QUERY,
                description="Filtra por first_name (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'last_name', openapi.IN_QUERY,
                description="Filtra por last_name (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description="Número de elementos por página (por defecto 10)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = User.objects.filter(status=True)
        filterset = UserFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs

        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class UserDetailAPIView(APIView):
    """
    - PUT: Actualiza los datos del usuario. Solo el propio usuario o un ADMIN pueden actualizar.
    - DELETE: Elimina al usuario. Solo el propio usuario o un ADMIN pueden eliminar.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @swagger_auto_schema(
        tags=["Users"],
        operation_summary="Actualizar usuario",
        operation_description="Actualiza los datos de un usuario. Solo el propio usuario o un ADMIN pueden realizar la actualización.",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def put(self, request, pk, *args, **kwargs):
        try:
            user_instance = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.pk != user_instance.pk and request.user.role != 'ADMIN':
            return Response(
                {"detail": "You do not have permission to update this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.serializer_class(user_instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Users"],
        operation_summary="Eliminar usuario",
        operation_description="Elimina un usuario. Solo el propio usuario o un ADMIN pueden realizar la eliminación.",
        responses={
            204: openapi.Response(description="User deleted successfully."),
            404: openapi.Response(description="User not found."),
            403: openapi.Response(description="Permission denied.")
        }
    )
    def delete(self, request, pk, *args, **kwargs):
        try:
            user_instance = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.pk != user_instance.pk and request.user.role != 'ADMIN':
            return Response(
                {"detail": "You do not have permission to delete this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_instance.status = False
        user_instance.save()
        return Response({"detail": "User deleted."}, status=status.HTTP_204_NO_CONTENT)


class ClientCreateAPIView(APIView):
    """
    Permite crear un nuevo cliente.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Clients'],
        operation_summary="Crear un nuevo cliente",
        operation_description="Registra un nuevo cliente con nombre, email y teléfono (opcional).",
        request_body=ClientSerializer,
        responses={
            201: ClientSerializer(),
            400: openapi.Response(description="Error en la validación"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientListAPIView(APIView):
    """
    Lista todos los clientes activos, permitiendo filtrar por nombre, email y teléfono.
    Se aplica paginación manual; por defecto se muestran 10 elementos (se puede modificar con el query param 'limit').
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Clients"],
        operation_summary="Listar clientes",
        operation_description=(
            "Obtiene la lista de clientes activos. Se pueden aplicar filtros mediante los query parameters:\n"
            "- name: búsqueda parcial en el nombre\n"
            "- email: búsqueda parcial en el email\n"
            "- phone: búsqueda parcial en el teléfono\n"
            "Se puede paginar usando el query param 'limit'."
        ),
        manual_parameters=[
            openapi.Parameter(
                'name', openapi.IN_QUERY,
                description="Filtrar por nombre (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'email', openapi.IN_QUERY,
                description="Filtrar por email (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'phone', openapi.IN_QUERY,
                description="Filtrar por teléfono (contiene)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description="Número de elementos por página (por defecto 10)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: ClientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = Client.objects.filter(status=True)
        filterset = ClientFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs
        
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ClientSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class ClientDetailAPIView(APIView):
    """
    Permite actualizar o eliminar un cliente.
    - PUT: Actualiza los datos del cliente.
    - DELETE: Realiza una eliminación, cambiando su campo 'status' a False.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Clients"],
        operation_summary="Actualizar cliente",
        operation_description="Actualiza los datos de un cliente. Solo el propio cliente (o un usuario con permisos especiales) puede actualizar.",
        request_body=ClientSerializer,
        responses={200: ClientSerializer()}
    )
    def put(self, request, pk, *args, **kwargs):

        client = Client.objects.filter(pk=pk, status=True).first()
        if not client:
            return Response({"detail": "Client not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ClientSerializer(client, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Clients"],
        operation_summary="Eliminar cliente",
        operation_description="Realiza una eliminación de un cliente, cambiando su campo 'status' a False.",
        responses={204: openapi.Response(description="Client  deleted.")}
    )
    def delete(self, request, pk, *args, **kwargs):
        
        client = Client.objects.filter(pk=pk, status=True).first()
        if not client:
            return Response({"detail": "Client not found or inactive."}, status=status.HTTP_404_NOT_FOUND)
        
        client.status = False
        client.save()
        return Response({"detail": "Client deleted."}, status=status.HTTP_204_NO_CONTENT)
    


class BulkClientUploadAPIView(APIView):
    """
    Endpoint para el cargue masivo de clientes.
    Permite subir un archivo CSV con un máximo de 20 registros (excluyendo el encabezado).
    La tarea se procesa de forma asíncrona mediante Celery.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Clients"],
        operation_summary="Cargue masivo de clientes",
        operation_description=(
            "Permite subir un archivo CSV para la creación masiva de clientes. "
            "El archivo debe tener un encabezado y las columnas: name, email, phone. "
            "Solo se permiten hasta 20 registros. Si se sobrepasa, se retorna un error."
        ),
        request_body=BulkClientUploadSerializer,
        responses={200: openapi.Response(description="Bulk upload initiated.")}
    )
    def post(self, request, *args, **kwargs):
        serializer = BulkClientUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        file.seek(0)
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file, delimiter=';')
        rows = list(reader)
        if not rows:
            return Response({"error": "The file is empty."}, status=status.HTTP_400_BAD_REQUEST)
        data_rows = rows[1:] if len(rows) > 1 else []
        if len(data_rows) > 20:
            return Response({"error": "The file cannot contain more than 20 records."}, status=status.HTTP_400_BAD_REQUEST)
        
        file.seek(0)
        temp_filename = f"bulk_clients.csv"
        upload_dir = os.path.join(settings.BASE_DIR, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, temp_filename)
        
        with open(file_path, "wb") as f:
            f.write(file.read())
        
        task = process_bulk_clients.delay(file_path, request.user.id)
        
        return Response({
            "task_id": task.id,
            "detail": "Bulk upload initiated."
        }, status=status.HTTP_200_OK)
    

class BulkClientUploadStatusAPIView(APIView):
    """
    Consulta el estado de la tarea de cargue masivo de clientes, incluyendo la cantidad de registros procesados y los errores (si existen).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Clients"],
        operation_summary="Consultar estado del cargue masivo",
        operation_description=(
            "Consulta el estado de la tarea de cargue masivo de clientes. Se debe enviar el 'task_id' asociado al cargue masivo. "
            "Si la tarea ya finalizó, se retornará un objeto con la cantidad de registros procesados y cualquier error encontrado."
        ),
        manual_parameters=[
            openapi.Parameter(
                'task_id',
                openapi.IN_QUERY,
                description="ID de la tarea de Celery asociada al cargue masivo",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: openapi.Response(description="Bulk upload status and errors.")}
    )
    def get(self, request, *args, **kwargs):
        task_id = request.GET.get("task_id")
        if not task_id:
            return Response({"error": "task_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        task_result = AsyncResult(task_id)
        if not task_result.ready():
            return Response({"status": task_result.state}, status=status.HTTP_202_ACCEPTED)
        
        result = task_result.result 
        return Response(result, status=status.HTTP_200_OK)    