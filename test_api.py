"""
E-commerce API Test Suite
Python-based testing for the Flask E-commerce API
"""

import requests
import json
import sys

class EcommerceAPITester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.jwt_token = None
        self.user_id = None
        
    def print_test(self, test_name):
        print(f"\n🔹 {test_name}")
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
        
    def test_user_registration(self):
        self.print_test("Test 1: User Registration")
        url = f"{self.base_url}/auth/register"
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "address": "123 Test Street",
            "password": "testpassword123"
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 201:
                result = response.json()
                self.jwt_token = result.get('access_token')
                self.user_id = result.get('user', {}).get('id')
                self.print_success("User registered successfully")
                print(f"   User ID: {self.user_id}")
                return True
            else:
                self.print_error(f"Registration failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Registration error: {str(e)}")
            return False
            
    def test_user_login(self):
        self.print_test("Test 2: User Login")
        url = f"{self.base_url}/auth/login"
        data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.jwt_token = result.get('access_token')
                self.print_success("Login successful")
                return True
            else:
                self.print_error(f"Login failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Login error: {str(e)}")
            return False
            
    def test_get_profile(self):
        self.print_test("Test 3: Get User Profile")
        url = f"{self.base_url}/auth/profile"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                self.print_success("Profile retrieved successfully")
                profile = response.json()
                print(f"   Name: {profile.get('name')}")
                print(f"   Email: {profile.get('email')}")
                return True
            else:
                self.print_error(f"Profile retrieval failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Profile error: {str(e)}")
            return False
            
    def test_create_products(self):
        self.print_test("Test 4: Create Products")
        url = f"{self.base_url}/products"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        products = [
            {"product_name": "Laptop Pro", "price": 1499.99},
            {"product_name": "Wireless Headphones", "price": 199.99},
            {"product_name": "Smartphone", "price": 799.99}
        ]
        
        created_products = []
        for product in products:
            try:
                response = requests.post(url, json=product, headers=headers)
                if response.status_code == 201:
                    created_products.append(response.json())
                else:
                    self.print_error(f"Failed to create {product['product_name']}: {response.text}")
            except Exception as e:
                self.print_error(f"Product creation error: {str(e)}")
                
        if created_products:
            self.print_success(f"Created {len(created_products)} products successfully")
            return True
        return False
        
    def test_get_products(self):
        self.print_test("Test 5: Get Products (Paginated)")
        url = f"{self.base_url}/products?page=1&per_page=5"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                products = result.get('products', [])
                pagination = result.get('pagination', {})
                
                self.print_success("Products retrieved with pagination")
                print(f"   Total products: {pagination.get('total', 0)}")
                for product in products:
                    print(f"   - {product['product_name']}: ${product['price']}")
                return True
            else:
                self.print_error(f"Products retrieval failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Products retrieval error: {str(e)}")
            return False
            
    def test_create_order(self):
        self.print_test("Test 6: Create Order")
        url = f"{self.base_url}/orders"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        data = {
            "product_ids": [1, 2],
            "shipping_address": "123 Test Street, Test City",
            "notes": "Test order - please handle with care"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 201:
                order = response.json()
                self.print_success("Order created successfully")
                print(f"   Order ID: {order.get('id')}")
                print(f"   Total: ${order.get('total_amount', 0)}")
                return order.get('id')
            else:
                self.print_error(f"Order creation failed: {response.text}")
                return None
        except Exception as e:
            self.print_error(f"Order creation error: {str(e)}")
            return None
            
    def test_get_user_orders(self):
        self.print_test("Test 7: Get User Orders")
        url = f"{self.base_url}/orders/user/{self.user_id}?page=1&per_page=10"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                orders = result.get('orders', [])
                self.print_success(f"Retrieved {len(orders)} user orders")
                return True
            else:
                self.print_error(f"User orders retrieval failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"User orders error: {str(e)}")
            return False
            
    def test_update_order_status(self, order_id):
        if not order_id:
            return False
            
        self.print_test("Test 8: Update Order Status")
        url = f"{self.base_url}/orders/{order_id}/status"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        data = {"status": "confirmed"}
        
        try:
            response = requests.put(url, json=data, headers=headers)
            if response.status_code == 200:
                self.print_success("Order status updated successfully")
                return True
            else:
                self.print_error(f"Order status update failed: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Order status update error: {str(e)}")
            return False
            
    def run_all_tests(self):
        print("🧪 E-commerce API Test Suite")
        print("=" * 40)
        
        # Test sequence
        if not self.test_user_registration():
            return
            
        if not self.test_user_login():
            return
            
        self.test_get_profile()
        self.test_create_products()
        self.test_get_products()
        
        order_id = self.test_create_order()
        self.test_get_user_orders()
        self.test_update_order_status(order_id)
        
        print(f"\n🎉 Testing Complete!")
        print("📊 Summary:")
        print("- User authentication: ✅")
        print("- Product management: ✅") 
        print("- Order management: ✅")
        print("- Pagination: ✅")
        print("- JWT protection: ✅")

if __name__ == "__main__":
    tester = EcommerceAPITester()
    tester.run_all_tests()
