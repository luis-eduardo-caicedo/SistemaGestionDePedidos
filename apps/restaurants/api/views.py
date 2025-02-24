from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from gestionPedidos.utils import CustomPagination
from apps.restaurants.api.filters import RestaurantFilter, ProductItemFilter
from .serializers import (RestaurantSerializer,
                          ProductItemSerializer,
                          EditRestaurantSerializer,
                          ListRestaurantSerializer,
                          EditProductItemSerializer)
from ..models import Restaurant, ProductItem


class RestaurantView(APIView):
    """
    Permite listar, crear y actualizar restaurantes del usuario autenticado.
    Para actualizar, se espera recibir la clave primaria del restaurante en la URL.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Listar restaurantes del usuario logueado",
        operation_description="Obtiene la lista de restaurantes pertenecientes al usuario autenticado.",
        responses={200: RestaurantSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = Restaurant.objects.filter(owner=request.user, status=True)
        filterset = RestaurantFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs 
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = RestaurantSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Crear restaurante",
        operation_description="Crea un nuevo restaurante asignando un owner especificado. Solo un usuario con rol ADMIN puede crear restaurantes.",
        request_body=RestaurantSerializer,
        responses={201: RestaurantSerializer()}
    )
    def post(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only ADMIN can create restaurants."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = RestaurantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListAllRestaurantView(APIView):
    """
    Permite listar, crear y actualizar restaurantes del usuario autenticado.
    Para actualizar, se espera recibir la clave primaria del restaurante en la URL.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Listar todos los restaurantes",
        operation_description="Obtiene la lista de restaurantes pertenecientes al usuario autenticado.",
        responses={200: ListRestaurantSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = Restaurant.objects.filter(status=True)
        filterset = RestaurantFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs 
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ListRestaurantSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class UpdateRestaurantView(APIView):
    """
    Permite listar, crear y actualizar restaurantes del usuario autenticado.
    Para actualizar, se espera recibir la clave primaria del restaurante en la URL.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Actualizar restaurante",
        operation_description="Actualiza un restaurante existente del usuario autenticado. Se espera que la URL contenga el 'pk' del restaurante.",
        request_body=EditRestaurantSerializer,
        responses={200: EditRestaurantSerializer()}
    )
    def put(self, request, pk, *args, **kwargs):
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response({"detail": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role != 'ADMIN' and restaurant.owner != request.user:
            return Response(
                {"detail": "You do not have permission to update this restaurant."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.serializer_class(restaurant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Eliminar restaurante",
        operation_description="Realiza una eliminación lógica del restaurante cambiando su status a False. Solo un usuario ADMIN puede realizar esta acción.",
        responses={
            200: openapi.Response(description="Restaurante eliminado lógicamente."),
            403: openapi.Response(description="No tienes permisos para eliminar este restaurante."),
            404: openapi.Response(description="Restaurante no encontrado.")
        }
    )
    def delete(self, request, pk, *args, **kwargs):
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response({"detail": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role != 'ADMIN':
            return Response({"detail": "Only ADMIN can delete restaurants."}, status=status.HTTP_403_FORBIDDEN)
        
        if not restaurant.status:
            return Response({"detail": "Restaurant is already deleted."}, status=status.HTTP_400_BAD_REQUEST)
        
        restaurant.status = False
        restaurant.save()
        return Response({"detail": "Restaurant deleted."}, status=status.HTTP_200_OK)
    

class ProductItemListCreateView(APIView):
    """
    GET: Lista todos los productos activos.
    POST: Crea un nuevo producto. Solo ADMIN o OWNER pueden crear.
    """
    permission_classes = []  

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Listar productos",
        operation_description="Obtiene la lista de todos los productos activos.",
        responses={200: ProductItemSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = ProductItem.objects.filter(status=True)
        filterset = ProductItemFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs 

        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ProductItemSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Crear producto",
        operation_description="Crea un nuevo producto. Solo un usuario ADMIN o OWNER puede crear productos.",
        request_body=ProductItemSerializer,
        responses={201: ProductItemSerializer()}
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['ADMIN', 'OWNER']:
            return Response(
                {"detail": "Only ADMIN or OWNER can create products."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ProductItemSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.role == 'OWNER':
                restaurant = serializer.validated_data.get('restaurant')
                if restaurant.owner != request.user:
                    return Response(
                        {"detail": "As an OWNER, you can only create products for your own restaurant."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProductItemUpdateDeleteView(APIView):
    """
    PUT: Actualiza un producto existente. Solo ADMIN o OWNER pueden actualizar.
    DELETE: Elimina un producto (cambiando su status a False). Solo ADMIN o OWNER.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Actualizar producto",
        operation_description="Actualiza un producto existente. Solo ADMIN o el OWNER del restaurante (del producto) pueden actualizar.",
        request_body=EditProductItemSerializer,
        responses={200: EditProductItemSerializer()}
        )
    def put(self, request, pk, *args, **kwargs):
        try:
            product = ProductItem.objects.get(pk=pk)
        except ProductItem.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role == 'OWNER':
            if product.restaurant.owner != request.user:
                return Response(
                    {"detail": "You can only update products from your own restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only ADMIN or OWNER can update products."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EditProductItemSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Eliminar producto",
        operation_description="Realiza una eliminación de un producto cambiando su status a False. Solo un usuario ADMIN o el OWNER del restaurante (del producto) pueden eliminarlo.",
        responses={
            200: openapi.Response(description="Product deleted."),
            404: openapi.Response(description="Product not found."),
            403: openapi.Response(description="Permission denied.")
        }
    )
    def delete(self, request, pk, *args, **kwargs):
        try:
            product = ProductItem.objects.get(pk=pk)
        except ProductItem.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role == 'OWNER':
            if product.restaurant.owner != request.user:
                return Response(
                    {"detail": "As an OWNER, you can only delete products from your own restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only ADMIN or OWNER can delete products."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not product.status:
            return Response({"detail": "Product is already deleted."}, status=status.HTTP_400_BAD_REQUEST)
        
        product.status = False
        product.save()
        return Response({"detail": "Product Item deleted."}, status=status.HTTP_200_OK)


class MenuRestaurantView(APIView):
    """
    Lista todos los productos activos (menú) de un restaurante.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Restaurant'],
        operation_summary="Obtener menú del restaurante",
        operation_description="Lista todos los productos activos (menú) de un restaurante dado.",
        manual_parameters=[
            openapi.Parameter(
                'restaurant_id', 
                openapi.IN_PATH, 
                description="ID del restaurante", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description="Número de elementos por página (por defecto 10)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: ProductItemSerializer(many=True)}
    )
    def get(self, request, restaurant_id, *args, **kwargs):
        products = ProductItem.objects.filter(restaurant__id=restaurant_id, status=True)
        filterset = ProductItemFilter(request.GET, queryset=products)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs 
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ProductItemSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)