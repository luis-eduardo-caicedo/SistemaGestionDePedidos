# Sistema de Gestión de Pedidos 🍽️

Este proyecto es un sistema de gestión de pedidos para restaurantes, desarrollado con Django y Django REST Framework. Permite gestionar usuarios, restaurantes, productos, órdenes y reportes de ventas.

## 📁 Estructura del Proyecto

```
gestionPedidos/
    ├── .env
    ├── apps/
    │   ├── orders/
    │   ├── restaurants/
    │   └── users/
    ├── docker-compose.yml
    ├── Dockerfile
    ├── gestionPedidos/
    ├── manage.py
    └── requirements.txt
```

## 🚀 Instalación

### Prerrequisitos

- Docker
- Docker Compose

### ⚙️ Configuración

1. Clona el repositorio:
```sh
git clone https://github.com/luis-eduardo-caicedo/SistemaGestionDePedidos.git
cd gestionPedidos
```

2. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables de entorno:
```env
# Variables de Django
DEBUG=True
DJANGO_SECRET_KEY='django-insecure-gh86o5-$snt4%b(4e$lrq$1(-0*aws0z90101n$3(+i7*dgzd@'

# Base de datos
POSTGRES_DB=gestionPedidos
POSTGRES_USER=postgresql
POSTGRES_PASSWORD=root
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Celery & Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 🏗️ Construcción y Ejecución

1. Construye y ejecuta los contenedores Docker:
```sh
docker-compose up --build
```

2. Inicializacion de datos ejemplo:
```sh
docker-compose run web python initdata.py
```

3. Crea un superusuario para acceder al panel de administración:
```sh
docker-compose run web python manage.py createsuperuser
```



## 🔄 Flujo de Uso del Sistema

### 1. Gestión de Usuarios

1. **Iniciar Sesión como Superusuario**
   - Usar el endpoint `POST /api/users/token/` para obtener el token de acceso

2. **Crear Usuarios**
   - Crear administradores y owners usando `POST /api/users/register/`
   - Los roles disponibles son: admin, owner, waitress

### 2. Configuración de Restaurante

1. **Crear Restaurante**
   - Usar `POST /api/restaurant/`
   - Asociar el restaurante con el owner correspondiente

2. **Gestionar Personal**
   - Crear meseros (waitress) usando `POST /api/users/register/`
   - Incluir el ID del restaurante en el JSON para la asociación

### 3. Gestión de Productos

1. **Crear Productos**
   - Usar `POST /api/restaurant/product-items/`
   - Asociar productos con el restaurante

2. **Consultar Menú**
   - Ver productos por restaurante: `GET /api/restaurant/menu/<restaurant_id>`

### 4. Gestión de Clientes

1. **Crear Clientes Individuales**
   - Usar `POST /api/users/clients/`

2. **Carga Masiva de Clientes**
   - Subir archivo: `POST /api/users/clients/bulk-upload/`
   - Verificar estado: `GET /api/users/clients/bulk-upload/status/`

### 5. Gestión de Órdenes y Reportes

1. **Crear Órdenes**
   - Usar `POST /api/order/create`
   - Incluir productos y cantidades

2. **Generar Reportes**
   - Solicitar generación: `POST /api/order/reports/generate/`
   - Consultar solicitudes: `GET /api/order/reports/requests/`
   - Descargar reporte: `GET /api/order/reports/download/` (usar task_id)

## 🔌 Endpoints Detallados

### 👥 Usuarios y Autenticación

- Obtener token: `POST /api/users/token/`
- Refrescar token: `POST /api/users/token/refresh/`
- Registro de usuario: `POST /api/users/register/`
- Cambiar contraseña: `POST /api/users/change-password/`
- Listar usuarios: `GET /api/users/list/`
- Detalle de usuario: `GET /api/users/<int:pk>`

### 👤 Gestión de Clientes

- Crear cliente: `POST /api/users/clients/`
- Listar clientes: `GET /api/users/clients/list/`
- Detalle de cliente: `GET /api/users/clients/<int:pk>/`
- Carga masiva: `POST /api/users/clients/bulk-upload/`
- Estado de carga: `GET /api/users/clients/bulk-upload/status/`

### 🏪 Restaurantes y Productos

- Crear/Listar restaurantes: `POST/GET /api/restaurant/`
- Listar todos los restaurantes: `GET /api/restaurant/all`
- Actualizar restaurante: `PUT /api/restaurant/<int:pk>`
- Gestionar productos: 
  - Crear/Listar: `POST/GET /api/restaurant/product-items/`
  - Actualizar/Eliminar: `PUT/DELETE /api/restaurant/product-items/<int:pk>`
- Ver menú: `GET /api/restaurant/menu/<int:restaurant_id>`

### 📝 Órdenes y Reportes

- Crear orden: `POST /api/order/create`
- Listar órdenes: `GET /api/order/list/<int:restaurant_id>`
- Detalle de orden: `GET /api/order/<int:restaurant_id>`
- Reportes:
  - Generar: `POST /api/order/reports/generate/`
  - Listar solicitudes: `GET /api/order/reports/requests/`
  - Descargar: `GET /api/order/reports/download/`

## 📚 Documentación de la API

La documentación completa de la API está disponible en:

- Swagger UI: [http://localhost:8000/docs/](http://localhost:8000/docs/)
- ReDoc: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

