# E-commerce Backend API

A RESTful API for managing an e-commerce system, built with **Django REST Framework** and **PostgreSQL**.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Django + Django REST Framework |
| Database | PostgreSQL |
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
python manage.py makemigrations
python manage.py migrate
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000`

---

## 📦 Product Model

| Field | Type | Rules |
|---|---|---|
| `id` | Integer | Auto-generated |
| `name` | String | Required, cannot be blank |
| `price` | Decimal | Required, must be greater than 0 |
| `description` | Text | Optional |
| `stock` | Integer | Cannot be negative |
| `created_at` | DateTime | Auto-set on creation |
| `updated_at` | DateTime | Auto-updated on every save |

---

## 🔗 API Endpoints

### Base URL
```
http://127.0.0.1:8000/api
```

---

### Products

#### Get All Products
```
GET /api/products/
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

#### Get Single Product
```
GET /api/products/<id>/
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

#### Create a Product
```
POST /api/products/
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
**Response `400 Bad Request`** *(validation failure)*
```json
{
    "price": ["Price must be greater than 0."]
}
```

---

#### Update a Product
```
PUT /api/products/<id>/
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

#### Delete a Product
```
DELETE /api/products/<id>/
```
**Response `200 OK`**
```json
{
    "message": "Product deleted successfully."
}
```

---

## ✅ Validation Rules

| Field | Rule | Error Message |
|---|---|---|
| `name` | Required, cannot be blank | `"Name cannot be blank."` |
| `price` | Must be greater than 0 | `"Price must be greater than 0."` |
| `stock` | Cannot be negative | `"Stock cannot be negative."` |

---

## 📁 Project Structure

```
ecommerce_backend/
├── manage.py
├── requirements.txt
├── .env                        (do not commit)
├── .gitignore
├── ecommerce_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── products/
    ├── migrations/
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── urls.py
```

---

## 🧪 Running Tests

Import the Postman collection (included in `/postman` folder) and run all requests against `http://127.0.0.1:8000`.

---

## 📌 Notes

- Never commit your `.env` file — it contains sensitive credentials
- Always run `makemigrations` and `migrate` after changing a model
- `DEBUG` should be set to `False` in production