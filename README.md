# E-commerce Backend API

A RESTful API for managing an e-commerce system, built with **Django REST Framework**, **PostgreSQL**, and **JWT Authentication**.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Django + Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT via SimpleJWT |
| Environment | python-dotenv |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ecommerce-backend.git
cd ecommerce-backend
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` File

In the root of the project, create a `.env` file and add the following:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True

DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Create the PostgreSQL Database

```sql
CREATE DATABASE ecommerce_db;
```

### 6. Run Migrations

```bash
python manage.py makemigrations users
python manage.py makemigrations products
python manage.py migrate
```

### 7. Create an Admin Account

```bash
python manage.py createsuperuser
```

Follow the prompts to set an email and password. This account will have `role = admin` and full access to all endpoints.

### 8. Start the Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000`

---

## 📁 Project Structure

```
ecommerce_backend/
├── manage.py
├── requirements.txt
├── .env                          ← secrets (do not commit)
├── .gitignore
├── postman/
│   └── ecommerce-api.postman_collection.json
├── ecommerce_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                        ← authentication & roles
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
└── products/                     ← product management
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

---

## 🔐 Authentication

This API uses **JWT (JSON Web Tokens)** for authentication.

### How it works

```
1. Sign up        → create an account
2. Log in         → receive an access token + refresh token
3. Make requests  → send access token in the Authorization header
4. Token expires  → use refresh token to get a new access token
5. Log out        → refresh token is blacklisted (invalidated)
```

### Using the token in requests

Add this header to every protected request:

```
Authorization: Bearer <your_access_token>
```

### Token Lifetimes

| Token | Lifetime | Purpose |
|---|---|---|
| Access Token | 5 minutes | Used to authenticate requests |
| Refresh Token | 1 day | Used to get a new access token |

> Once the refresh token expires, the user must log in again.

---

## 👥 Roles & Permissions

There are two roles in the system:

| Role | Assigned To | Permissions |
|---|---|---|
| `admin` | Created via `createsuperuser` or manually set | Full CRUD on products |
| `user` | Anyone who signs up normally | Read-only access to products |

### Permission Map

| Endpoint | No Token | User Token | Admin Token |
|---|---|---|---|
| `POST /api/auth/signup/` | ✅ | ✅ | ✅ |
| `POST /api/auth/login/` | ✅ | ✅ | ✅ |
| `POST /api/auth/logout/` | ❌ 401 | ✅ | ✅ |
| `GET /api/auth/profile/` | ❌ 401 | ✅ | ✅ |
| `GET /api/products/` | ❌ 401 | ✅ | ✅ |
| `POST /api/products/` | ❌ 401 | ❌ 403 | ✅ |
| `GET /api/products/<id>/` | ❌ 401 | ✅ | ✅ |
| `PUT /api/products/<id>/` | ❌ 401 | ❌ 403 | ✅ |
| `DELETE /api/products/<id>/` | ❌ 401 | ❌ 403 | ✅ |

> **401 Unauthorized** — no token provided or token is invalid.
> **403 Forbidden** — valid token but insufficient role.

---

## 🔗 API Endpoints

### Base URL
```
http://127.0.0.1:8000/api
```

---

## 🔐 Auth Endpoints

### Sign Up
```
POST /api/auth/signup/
```
**Request Body**
```json
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepass123",
    "password2": "securepass123"
}
```
**Response `201 Created`**
```json
{
    "message": "Account created successfully.",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "role": "user"
    },
    "tokens": {
        "refresh": "eyJhbGci...",
        "access": "eyJhbGci..."
    }
}
```

---

### Login
```
POST /api/auth/login/
```
**Request Body**
```json
{
    "email": "user@example.com",
    "password": "securepass123"
}
```
**Response `200 OK`**
```json
{
    "message": "Login successful.",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "role": "user"
    },
    "tokens": {
        "refresh": "eyJhbGci...",
        "access": "eyJhbGci..."
    }
}
```

---

### Logout
```
POST /api/auth/logout/
Authorization: Bearer <access_token>
```
**Request Body**
```json
{
    "refresh": "eyJhbGci..."
}
```
**Response `200 OK`**
```json
{
    "message": "Logged out successfully."
}
```

---

### View Profile
```
GET /api/auth/profile/
Authorization: Bearer <access_token>
```
**Response `200 OK`**
```json
{
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 📦 Product Endpoints

### Get All Products
```
GET /api/products/
Authorization: Bearer <access_token>
```
**Response `200 OK`**
```json
[
    {
        "id": 1,
        "name": "Wireless Headphones",
        "price": "49.99",
        "description": "Noise cancelling over-ear headphones",
        "stock": 100,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
]
```

---

### Get Single Product
```
GET /api/products/<id>/
Authorization: Bearer <access_token>
```
**Response `200 OK`**
```json
{
    "id": 1,
    "name": "Wireless Headphones",
    "price": "49.99",
    "description": "Noise cancelling over-ear headphones",
    "stock": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```
**Response `404 Not Found`**
```json
{
    "error": "Product not found."
}
```

---

### Create a Product
```
POST /api/products/
Authorization: Bearer <access_token>   ← admin only
```
**Request Body**
```json
{
    "name": "Wireless Headphones",
    "price": "49.99",
    "description": "Noise cancelling over-ear headphones",
    "stock": 100
}
```
**Response `201 Created`**
```json
{
    "id": 1,
    "name": "Wireless Headphones",
    "price": "49.99",
    "description": "Noise cancelling over-ear headphones",
    "stock": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```
**Response `403 Forbidden`** *(non-admin user)*
```json
{
    "detail": "Access denied. Admin privileges required to modify products."
}
```

---

### Update a Product
```
PUT /api/products/<id>/
Authorization: Bearer <access_token>   ← admin only
```
**Request Body**
```json
{
    "name": "Wireless Headphones Pro",
    "price": "79.99",
    "description": "Upgraded noise cancelling headphones",
    "stock": 50
}
```
**Response `200 OK`**
```json
{
    "id": 1,
    "name": "Wireless Headphones Pro",
    "price": "79.99",
    "description": "Upgraded noise cancelling headphones",
    "stock": 50,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
}
```

---

### Delete a Product
```
DELETE /api/products/<id>/
Authorization: Bearer <access_token>   ← admin only
```
**Response `200 OK`**
```json
{
    "message": "Product deleted successfully."
}
```

---

## ✅ Validation Rules

### User
| Field | Rule |
|---|---|
| `email` | Required, must be unique |
| `password` | Required, minimum 8 characters |
| `password2` | Must match `password` |

### Product
| Field | Rule | Error |
|---|---|---|
| `name` | Required, cannot be blank | `"Name cannot be blank."` |
| `price` | Must be greater than 0 | `"Price must be greater than 0."` |
| `stock` | Cannot be negative | `"Stock cannot be negative."` |

---

## 🧪 Testing

Import the Postman collection from the `/postman` folder.

### Recommended test flow
1. `POST /api/auth/signup/` — create a regular user
2. `POST /api/auth/login/` — login and save tokens
3. `GET /api/products/` — confirm user can read
4. `POST /api/products/` — confirm user gets 403
5. Login as admin → repeat steps 3 & 4 to confirm full access
6. `POST /api/auth/logout/` — blacklist the refresh token
7. Reuse the refresh token — confirm 400 error

---

## 📌 Notes

- Never commit your `.env` file — it contains sensitive credentials
- Always run `makemigrations users` before `makemigrations products`
- `DEBUG` should be set to `False` in production
- Access tokens expire in 5 minutes — use the refresh token to get a new one
- Once logged out, the refresh token is permanently invalidated