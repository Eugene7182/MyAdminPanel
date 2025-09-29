import time
import json
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# --- Configuration and Setup ---

# Initializing the FastAPI application
app = FastAPI(title="Admin Panel Mock Backend API")

# Define allowed origins for CORS (Cross-Origin Resource Sharing)
# MUST include '*' for development, or the specific address where the React app runs.
origins = [
    "http://localhost",
    "http://localhost:3000",  # Common React development port
    "http://localhost:8080",
    "*"  # Allowing all origins for simple testing/Canvas environment
]

# Adding CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy OAuth2 security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- Dummy Data Structures (Simulating a Database) ---

class Tag(BaseModel):
    title: str
    type: str

class Category(BaseModel):
    id: int
    name: str

class Product(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    price: float
    is_active: bool
    category_id: int
    tag_ids: List[int]

class ProductResponse(Product):
    category: Optional[Category] = None
    tags: List[Tag] = []

class UserPermissions(BaseModel):
    permissions: List[str] = []

# Mock database
mock_categories = {
    1: Category(id=1, name="Electronics"),
    2: Category(id=2, name="Clothing"),
    3: Category(id=3, name="Home Goods"),
}

mock_tags = {
    101: Tag(title="New Arrival", type="promo"),
    102: Tag(title="Sale", type="promo"),
    103: Tag(title="Summer", type="season"),
}

mock_products: Dict[int, Product] = {
    1: Product(id=1, sku="EL-1001", name="Laptop Pro", description="High-end laptop", price=1200.50, is_active=True, category_id=1, tag_ids=[101]),
    2: Product(id=2, sku="CL-205", name="T-Shirt Basic", description="Cotton t-shirt", price=15.99, is_active=True, category_id=2, tag_ids=[102, 103]),
    3: Product(id=3, sku="HG-44", name="Smart Lamp", description="Voice controlled lamp", price=85.00, is_active=False, category_id=3, tag_ids=[]),
    4: Product(id=4, sku="EL-1002", name="Monitor 4K", description="27 inch monitor", price=350.00, is_active=True, category_id=1, tag_ids=[]),
    5: Product(id=5, sku="CL-206", name="Jeans Slim", description="Blue denim", price=110.00, is_active=True, category_id=2, tag_ids=[101]),
}

# --- Utility Functions ---

def get_product_response(product: Product) -> ProductResponse:
    """Combines a product with its related category and tags."""
    category = mock_categories.get(product.category_id)
    tags = [mock_tags[tid] for tid in product.tag_ids if tid in mock_tags]
    return ProductResponse(**product.model_dump(), category=category, tags=tags)


# V6.0: Filter Parsing and Application
def apply_filters(items: List[Any], entity: str, filter_strings: List[str]) -> List[Any]:
    """Applies V6.0 filters (e.g., 'price:gt:100') to the list of items."""
    if not filter_strings:
        return items

    filtered_items = []
    
    for item in items:
        passes_all_filters = True
        
        for f_str in filter_strings:
            try:
                field, operator, value_str = f_str.split(':', 2)
            except ValueError:
                # Skip invalid filter format
                continue

            # Determine the correct type for comparison
            # Note: This is a simplified type check based on the field name
            if field in ['price']:
                value = float(value_str)
            elif field in ['is_active']:
                value = value_str.lower() == 'true'
            else:
                value = value_str

            item_value = getattr(item, field, None)

            if item_value is None:
                passes_all_filters = False
                break
                
            # Apply the operator logic
            if operator == 'eq':
                if item_value != value:
                    passes_all_filters = False
            elif operator == 'gt':
                if not (item_value > value):
                    passes_all_filters = False
            elif operator == 'lt':
                if not (item_value < value):
                    passes_all_filters = False
            elif operator == 'contains':
                # Simplified case-insensitive string contains check
                if not (isinstance(item_value, str) and value.lower() in item_value.lower()):
                    passes_all_filters = False
            
            if not passes_all_filters:
                break

        if passes_all_filters:
            filtered_items.append(item)
            
    return filtered_items


# --- Dependency: Mock User Authentication ---

def mock_get_current_user(token: str = Depends(oauth2_scheme)):
    """Mocks JWT token validation."""
    # In a real app, this would validate the token and return the user object.
    # We use a simple time-based check to simulate a successful login.
    if token.startswith("header."): # Simple check for our mock token format
        # Simulate user data, essential for WS connection (userId in the React code)
        return {"username": "admin@example.com", "sub": "admin_user_id"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# --- Endpoint Handlers ---

@app.post("/auth/token")
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    """Handles user login and returns a mock JWT token."""
    # Simple check: any non-empty user/pass works for the mock
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Mock JWT Payload (Base64url encoded for simplicity, simulating real token structure)
    # Payload: {"sub": "admin_user_id", "exp": 1678886400}
    mock_payload = 'eyJzdWIiOiJhZG1pbl91c2VyX2lkIiwiZXhwIjoxNjc4ODg2NDAwfQ'
    mock_jwt = f"header.{mock_payload}.signature"
    return {"access_token": mock_jwt, "token_type": "bearer"}


@app.get("/auth/permissions/me", response_model=UserPermissions)
def get_user_permissions(current_user: dict = Depends(mock_get_current_user)):
    """V5.1: Returns mock permissions for the logged-in user."""
    # Mock permissions: full CRUD access for the admin user
    return UserPermissions(permissions=["create", "read", "update", "delete"])


@app.get("/products/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[str] = None,  # V6.0 Filter parameter
    current_user: dict = Depends(mock_get_current_user)
):
    """Retrieves and filters products."""
    
    products_list = list(mock_products.values())
    
    # V6.0: Apply filtering logic
    if filters:
        filter_strings = filters.split(',')
        products_list = apply_filters(products_list, 'products', filter_strings)
    
    # Apply relations and pagination
    products_response = [get_product_response(p) for p in products_list]
    return products_response[skip: skip + limit]

@app.get("/categories/", response_model=List[Category])
def read_categories(
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[str] = None,  # V6.0 Filter parameter
    current_user: dict = Depends(mock_get_current_user)
):
    """Retrieves and filters categories."""
    
    categories_list = list(mock_categories.values())
    
    # V6.0: Apply filtering logic (simplified: only name:contains supported in mock)
    if filters:
        filter_strings = filters.split(',')
        categories_list = apply_filters(categories_list, 'categories', filter_strings)

    return categories_list[skip: skip + limit]

# --- V4.2: WebSocket Manager (Real-time) ---

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        # Dictionary to store connections by user ID: {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"WS: User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            print(f"WS: User {user_id} disconnected.")

    async def broadcast(self, user_id: str, message: Dict[str, str]):
        """Sends a message to all active sessions of a specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)
                
manager = ConnectionManager()

# Mock function to simulate a database change (and trigger a WS update)
async def simulate_db_change(user_id: str, entity: str):
    """Triggers a WS broadcast after a mock data change."""
    await manager.broadcast(
        user_id, 
        {"message": f"Data change detected in {entity}", "entity": entity, "timestamp": time.time()}
    )

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Handles WebSocket connections for real-time updates for a specific user."""
    await manager.connect(websocket, user_id)
    try:
        # Keep the connection alive, waiting for messages (e.g., pings from client)
        while True:
            # We don't expect the client to send messages in this design, 
            # but we need to receive to keep the connection open.
            data = await websocket.receive_text()
            # If a message is received, we can optionally process it
            # print(f"Received from {user_id}: {data}") 
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# --- Mock CRUD operations (to simulate changes that trigger WS) ---
# NOTE: These endpoints are simplified and do not fully implement error handling or validation

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(mock_get_current_user)):
    if product_id not in mock_products:
        raise HTTPException(status_code=404, detail="Product not found")
    del mock_products[product_id]
    
    # Simulate a successful response and trigger WS update
    await simulate_db_change(current_user["sub"], "products")
    return {"message": "Product deleted successfully"}
