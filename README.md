# E-commerce API

A REST API for e-commerce built with Flask, SQLAlchemy, and MySQL.

## Features

- JWT Authentication
- User, Product, and Order management
- Pagination and search
- Order status tracking
- Data validation

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup MySQL database**
   - Create database named `ecommerce_api`
   - Update connection string in `app.py`

3. **Run the API**
   ```bash
   python app.py
   ```
   Server runs on `http://localhost:5001`

## API Endpoints

### Authentication
- `POST /auth/register` - Register user
- `POST /auth/login` - Login user
- `GET /auth/profile` - Get profile (JWT required)

### Products
- `GET /products` - List products
- `POST /products` - Create product (JWT required)
- `PUT /products/<id>` - Update product (JWT required)

### Orders
- `POST /orders` - Create order (JWT required)
- `GET /orders/user/<id>` - Get user orders (JWT required)
- `PUT /orders/<id>/status` - Update status (JWT required)

## Testing

Run the test suite:
```bash
python test_api.py
```

Or check health:
```bash
python health_check.py
```
