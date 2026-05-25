# E-commerce Backend API

A fully functional e-commerce backend built with **Django REST Framework**, **PostgreSQL**, **JWT Authentication**, and **Paystack payment integration**.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Django + Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT via SimpleJWT |
| Payments | Paystack (test mode) |
| Email | Gmail SMTP |
| Environment | python-dotenv |
| Logging | Python logging module |

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

In the root of the project, create a `.env` file:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Database
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Paystack
PAYSTACK_SECRET_KEY=your_paystack_secret_key_here
PAYSTACK_BASE_URL=https://api.paystack.co

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your_gmail@gmail.com
```

### 5. Create the PostgreSQL Database

```sql
CREATE DATABASE ecommerce_db;
```

### 6. Run Migrations

```bash
python manage.py makemigrations users
python manage.py makemigrations products
python manage.py makemigrations orders
python manage.py migrate
```

### 7. Create an Admin Account

```bash
python manage.py createsuperuser
```

This account will have `role = admin` and full access to all endpoints.

### 8. Start the Development Server

```bash
python manage.py runserver
```

API available at: `http://127.0.0.1:8000`

Logs available at: `logs/orders.log`

---

## 📁 Project Structure

```
ecommerce_backend/
├── manage.py
├── requirements.txt
├── .env                              ← secrets (never commit)
├── .gitignore
├── logs/
│   └── orders.log                    ← auto-created on first run
├── postman/
│   └── ecommerce-api.postman_collection.json
├── ecommerce_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                            ← authentication & roles
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
├── products/                         ← product management
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── orders/                           ← orders & payments
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── services.py                   ← business logic layer
    └── logger.py                     ← logging setup
```

---

## 🔐 Authentication

This API uses **JWT (JSON Web Tokens)** for authentication.

### Auth Flow

```
1. Sign up        → create an account (role defaults to 'user')
2. Log in         → receive access token + refresh token
3. Make requests  → send access token in Authorization header
4. Token expires  → use refresh token to get a new access token
5. Log out        → refresh token is blacklisted permanently
```

### Using the Token

```
Authorization: Bearer <your_access_token>
```

### Token Lifetimes

| Token | Lifetime | Purpose |
|---|---|---|
| Access Token | 5 minutes | Authenticates requests |
| Refresh Token | 1 day | Gets a new access token |

---

## 👥 Roles & Permissions

| Role | Assigned To | Permissions |
|---|---|---|
| `admin` | Created via `createsuperuser` | Full CRUD on products |
| `user` | Anyone who signs up | Read products, place orders |

### Permission Map

| Endpoint | No Token | User | Admin |
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
| `GET /api/orders/` | ❌ 401 | ✅ own only | ✅ |
| `POST /api/orders/` | ❌ 401 | ✅ | ✅ |
| `GET /api/orders/<id>/` | ❌ 401 | ✅ own only | ✅ |
| `POST /api/orders/<id>/pay/` | ❌ 401 | ✅ own only | ✅ |
| `POST /api/orders/<id>/verify/` | ❌ 401 | ✅ own only | ✅ |

---

## 🛒 Order Lifecycle

Every order moves through the following states:

```
User creates order
        │
        ▼
  status: PENDING          ← order exists, awaiting payment
        │
        ▼
  Payment initiated        ← Paystack checkout URL generated
        │
        ▼
  User pays on Paystack    ← test card entered on Paystack page
        │
        ▼
  Payment verified         ← server confirms with Paystack
        │
        ├── success → status: PAID     + confirmation email sent
        └── failure → status: FAILED   + user can retry with new order
```

### What happens at each stage

**Order Creation:**
- Validates all products exist
- Validates sufficient stock for each item
- Snapshots the product price at time of order (price changes won't affect old orders)
- Deducts stock immediately on order creation
- Calculates and stores total automatically

**Payment Initiation:**
- Converts total to kobo (smallest currency unit)
- Generates a unique payment reference
- Calls Paystack `/transaction/initialize`
- Returns a Paystack checkout URL for the user

**Payment Verification:**
- Calls Paystack `/transaction/verify/{reference}` server-to-server
- Never trusts the client to report payment result
- Updates order status to `paid` or `failed`
- Sends confirmation email on successful payment

---

## 💳 Payment Integration

This API integrates with **Paystack** in test mode.

### How it works

```
Our Server                         Paystack
──────────                         ────────
POST /transaction/initialize  ──→  Creates payment session
                              ←──  Returns authorization_url

User visits authorization_url ──→  Enters card on Paystack page
                                   Paystack processes payment

GET /transaction/verify/{ref} ──→  Confirms payment result
                              ←──  Returns status: success/failed
```

### Test Card Details

Use these on the Paystack checkout page during testing:

| Field | Value |
|---|---|
| Card Number | `4084 0840 8408 4081` |
| Expiry | Any future date |
| CVV | `408` |
| PIN | `0000` |
| OTP (success) | `123456` |
| OTP (failure) | `000000` |

### Getting Your Paystack Test Key

1. Sign up at **paystack.com** (free)
2. Dashboard → Settings → API Keys & Webhooks
3. Copy the **Secret Key** starting with `sk_test_`
4. Add it to your `.env` as `PAYSTACK_SECRET_KEY`

---

## ⚠️ Error Handling

The API handles errors at multiple levels:

### Validation Errors — `400 Bad Request`
Returned when the client sends invalid data:
```json
{ "items": ["Order must contain at least one item."] }
{ "quantity": ["Not enough stock for 'Wireless Headphones'. Available: 5, Requested: 10."] }
{ "price": ["Price must be greater than 0."] }
```

### Authentication Errors — `401 Unauthorized`
Returned when no token or an invalid token is provided:
```json
{ "detail": "Authentication credentials were not provided." }
```

### Permission Errors — `403 Forbidden`
Returned when a user attempts an action above their role:
```json
{ "detail": "Access denied. Admin privileges required to modify products." }
```

### Not Found Errors — `404 Not Found`
Returned when a resource doesn't exist or belongs to another user:
```json
{ "error": "Order not found." }
```

### Gateway Errors — `502 Bad Gateway`
Returned when Paystack is unreachable or returns an error:
```json
{ "error": "Payment gateway timed out. Please try again." }
```

### State Errors — `400 Bad Request`
Returned when an action isn't valid for the current state:
```json
{ "error": "This order cannot be paid. Current status: paid." }
```

---

## 📋 Logging

All order and payment activity is logged to `logs/orders.log`:

```
[2024-01-15 10:30:00] INFO  orders.services — Creating order for user: user@test.com
[2024-01-15 10:30:00] INFO  orders.services — Item added: 2 × Wireless Headphones @ 49.99
[2024-01-15 10:30:00] INFO  orders.services — Order #1 created — total: 119.97 — status: pending
[2024-01-15 10:31:00] INFO  orders.services — Initiating payment for Order #1 — reference: ORDER-1-A3F9B2C1
[2024-01-15 10:32:00] INFO  orders.services — Order #1 marked as PAID — reference: ORDER-1-A3F9B2C1
[2024-01-15 10:32:01] INFO  orders.services — Confirmation email sent to user@test.com
```

Log levels used:

| Level | When |
|---|---|
| `INFO` | Normal operations — order created, payment verified, email sent |
| `WARNING` | Unexpected but not broken — double payment attempt, invalid order data |
| `ERROR` | Something broke — Paystack timeout, email delivery failure |

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
```json
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepass123",
    "password2": "securepass123"
}
```

### Login
```
POST /api/auth/login/
```
```json
{
    "email": "user@example.com",
    "password": "securepass123"
}
```

### Logout
```
POST /api/auth/logout/
Authorization: Bearer <access_token>
```
```json
{ "refresh": "eyJhbGci..." }
```

### Profile
```
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

---

## 📦 Product Endpoints

### Get All Products
```
GET /api/products/
Authorization: Bearer <access_token>
```

### Get Single Product
```
GET /api/products/<id>/
Authorization: Bearer <access_token>
```

### Create Product (Admin only)
```
POST /api/products/
Authorization: Bearer <access_token>
```
```json
{
    "name": "Wireless Headphones",
    "price": "49.99",
    "description": "Noise cancelling headphones",
    "stock": 100
}
```

### Update Product (Admin only)
```
PUT /api/products/<id>/
Authorization: Bearer <access_token>
```

### Delete Product (Admin only)
```
DELETE /api/products/<id>/
Authorization: Bearer <access_token>
```

---

## 🛒 Order Endpoints

### Create Order
```
POST /api/orders/
Authorization: Bearer <access_token>
```
```json
{
    "items": [
        { "product_id": 1, "quantity": 2 },
        { "product_id": 2, "quantity": 1 }
    ]
}
```
**Response `201 Created`:**
```json
{
    "id": 1,
    "user_email": "user@example.com",
    "status": "pending",
    "total_price": "119.97",
    "payment_reference": null,
    "items": [
        {
            "id": 1,
            "product": 1,
            "product_name": "Wireless Headphones",
            "quantity": 2,
            "unit_price": "49.99",
            "subtotal": "99.98"
        }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### Get All Orders
```
GET /api/orders/
Authorization: Bearer <access_token>
```
Returns only orders belonging to the authenticated user.

### Get Single Order
```
GET /api/orders/<id>/
Authorization: Bearer <access_token>
```

### Initiate Payment
```
POST /api/orders/<id>/pay/
Authorization: Bearer <access_token>
```
**Response `200 OK`:**
```json
{
    "message": "Payment initiated successfully.",
    "order_id": 1,
    "authorization_url": "https://checkout.paystack.com/0peioxfhpn",
    "reference": "ORDER-1-A3F9B2C1"
}
```

### Verify Payment
```
POST /api/orders/<id>/verify/
Authorization: Bearer <access_token>
```
```json
{ "reference": "ORDER-1-A3F9B2C1" }
```
**Response `200 OK`:**
```json
{
    "message": "Payment verified successfully.",
    "order": {
        "id": 1,
        "status": "paid",
        "payment_reference": "ORDER-1-A3F9B2C1",
        ...
    }
}
```

---

## ✅ Validation Rules

### User
| Field | Rule |
|---|---|
| `email` | Required, unique |
| `password` | Required, minimum 8 characters |
| `password2` | Must match `password` |

### Product
| Field | Rule |
|---|---|
| `name` | Required, cannot be blank |
| `price` | Required, must be greater than 0 |
| `stock` | Cannot be negative |

### Order
| Field | Rule |
|---|---|
| `items` | At least one item required |
| `product_id` | Product must exist |
| `quantity` | Minimum 1, cannot exceed available stock |
| Duplicates | Each product can appear only once per order |

---

## 🧪 Testing

Import the Postman collection from `/postman` folder.

### Recommended Full Flow

```
1.  POST /api/auth/login/              (admin)     → save admin token
2.  POST /api/products/                (admin)     → create products
3.  POST /api/auth/login/              (user)      → save user token
4.  POST /api/orders/                  (user)      → create order, save order ID
5.  POST /api/orders/<id>/pay/         (user)      → get authorization_url
6.  Visit authorization_url in browser             → pay with test card
7.  POST /api/orders/<id>/verify/      (user)      → confirm payment
8.  Check email inbox                              → confirmation email
9.  GET  /api/orders/<id>/             (user)      → status = paid
10. POST /api/orders/<id>/pay/         (user)      → confirm 400 (already paid)
```

---

## 📌 Notes

- Never commit your `.env` file
- Always run `makemigrations users` before `makemigrations products` and `orders`
- Set `DEBUG=False` in production
- Access tokens expire in 5 minutes — use refresh token to get a new one
- Stock is deducted at order creation, not at payment
- Email failures are logged but never block the payment response
- All amounts are stored in Naira (₦) but sent to Paystack in kobo