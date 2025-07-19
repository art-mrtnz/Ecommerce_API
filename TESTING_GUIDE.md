# E-commerce API Testing Guide

## 🚀 How to Test Your E-commerce API

Your e-commerce API is fully functional with JWT authentication, pagination, and advanced order management. Here are several ways to test it:

### **Prerequisites**
- API is running on `http://localhost:5001`
- Database is initialized (run `curl -X POST http://localhost:5001/init-db` if needed)

---

## **Method 1: Using Postman (Recommended)**

### Import the Collections
1. Open Postman
2. Import these files from your project directory:
   - `Ecommerce_API_Enhanced_Collection.postman_collection.json`
   - `Ecommerce_API_Environment.postman_environment.json`

### Testing Sequence
1. **Register a User**: POST `/auth/register`
2. **Login**: POST `/auth/login` (saves JWT token automatically)
3. **Create Products**: POST `/products` (JWT required)
4. **Create Orders**: POST `/orders` (JWT required)
5. **Test Pagination**: GET `/products?page=1&per_page=5`
6. **Advanced Order Management**: Update status, cancel orders, etc.

---

## **Method 2: Using curl Commands**

### Step 1: Register a User
```bash
curl -X POST http://localhost:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "user@example.com", 
    "address": "123 Test Street",
    "password": "password123"
  }'
```

### Step 2: Login and Get JWT Token
```bash
TOKEN=$(curl -s -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "JWT Token: $TOKEN"
```

### Step 3: Create Products (JWT Required)
```bash
curl -X POST http://localhost:5001/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "product_name": "Gaming Laptop",
    "price": 1299.99
  }'

curl -X POST http://localhost:5001/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "product_name": "Wireless Mouse", 
    "price": 49.99
  }'
```

### Step 4: Get Products with Pagination
```bash
curl "http://localhost:5001/products?page=1&per_page=5"
```

### Step 5: Create an Order (JWT Required)
```bash
curl -X POST http://localhost:5001/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "product_ids": [1, 2],
    "shipping_address": "123 Test Street",
    "notes": "Test order"
  }'
```

### Step 6: Get User Orders (JWT Required)
```bash
curl "http://localhost:5001/orders/user/1?page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 7: Update Order Status (JWT Required)
```bash
curl -X PUT http://localhost:5001/orders/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "confirmed"}'
```

---

## **Method 3: Using Python Script**

Run the provided test script:
```bash
python3 test_api.py
```

---

## **Method 4: Manual Testing with Browser/HTTP Client**

### Public Endpoints (No Authentication Required)
- `GET http://localhost:5001/` - API documentation
- `GET http://localhost:5001/products` - Get all products (paginated)
- `GET http://localhost:5001/products/1` - Get specific product

### Authentication Endpoints
- `POST http://localhost:5001/auth/register` - Register new user
- `POST http://localhost:5001/auth/login` - Login user

### Protected Endpoints (JWT Required)
- `GET http://localhost:5001/auth/profile` - Get current user profile
- `POST http://localhost:5001/products` - Create product
- `PUT http://localhost:5001/products/1` - Update product
- `DELETE http://localhost:5001/products/1` - Delete product
- `POST http://localhost:5001/orders` - Create order
- `GET http://localhost:5001/orders` - Get all orders (paginated)
- `PUT http://localhost:5001/orders/1/status` - Update order status
- `PUT http://localhost:5001/orders/1/cancel` - Cancel order

---

## **Key Features to Test**

### ✅ **JWT Authentication**
- User registration and login
- JWT token generation and validation
- Protected endpoints requiring authentication

### ✅ **Pagination**
- `GET /users?page=1&per_page=10`
- `GET /products?page=1&per_page=5&search=laptop`
- `GET /orders?page=1&per_page=10`

### ✅ **Advanced Order Management**
- Order status tracking (pending, confirmed, shipped, delivered, cancelled)
- Order cancellation
- Status-based filtering: `GET /orders/status/pending`
- Total amount calculation

### ✅ **Data Validation**
- Email format validation
- Price range validation
- Required field validation
- Duplicate prevention

### ✅ **Security Features**
- Users can only access their own data
- Password hashing with bcrypt
- Email uniqueness validation
- Status-based operation restrictions

---

## **Troubleshooting**

### Database Issues
```bash
# Reset database
mysql -u root -pMrtnz81! -e "DROP DATABASE ecommerce_api; CREATE DATABASE ecommerce_api;"
curl -X POST http://localhost:5001/init-db
```

### API Not Responding
```bash
# Check if API is running
curl http://localhost:5001/

# Restart the API
python app.py
```

### JWT Token Issues
- Make sure to include `Bearer ` prefix in Authorization header
- Check token expiration (24 hours by default)
- Re-login to get a fresh token

---

## **Sample Test Data**

### Users
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "address": "123 Main St, Anytown USA", 
  "password": "password123"
}
```

### Products
```json
{
  "product_name": "Gaming Laptop",
  "price": 1299.99
}
```

### Orders
```json
{
  "product_ids": [1, 2],
  "shipping_address": "456 Oak Street",
  "notes": "Please deliver during business hours"
}
```

---

## **API Endpoints Summary**

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/` | No | API documentation |
| POST | `/auth/register` | No | Register user |
| POST | `/auth/login` | No | Login user |
| GET | `/auth/profile` | Yes | Get user profile |
| GET | `/products` | No | Get products (paginated) |
| POST | `/products` | Yes | Create product |
| GET | `/products/{id}` | No | Get specific product |
| PUT | `/products/{id}` | Yes | Update product |
| DELETE | `/products/{id}` | Yes | Delete product |
| POST | `/orders` | Yes | Create order |
| GET | `/orders` | Yes | Get all orders (paginated) |
| GET | `/orders/{id}` | Yes | Get specific order |
| PUT | `/orders/{id}/status` | Yes | Update order status |
| PUT | `/orders/{id}/cancel` | Yes | Cancel order |
| GET | `/orders/status/{status}` | Yes | Get orders by status |
| GET | `/orders/user/{user_id}` | Yes | Get user orders |

Your API is production-ready with comprehensive features! 🎉
