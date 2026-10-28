# Kitchen Menu & Order Router — API Documentation

## 1. Overview

This project uses a Flask REST API to manage kitchen menu items and customer orders. SQLite is used to store menu, order and order item information.

**Base URL:** `http://127.0.0.1:5000/api`

The API supports adding menu items, checking availability, placing orders for specific tables, viewing orders and updating order status.

## 2. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/menu` | Get all menu items |
| GET | `/menu/active` | Get available menu items |
| POST | `/menu` | Add a menu item |
| PATCH | `/menu/{item_id}/availability` | Update item availability |
| POST | `/orders` | Place a new order with a table number |
| GET | `/orders` | Get all orders |
| GET | `/orders/{order_id}` | Get a specific order |
| PATCH | `/orders/{order_id}/status` | Move an order to the next status |

## 3. Menu APIs

### 3.1 Get All Menu Items

**Endpoint:** `GET /api/menu`

Returns all menu items, including unavailable items, ordered by ID.

Example response:

```json
[
  {
    "id": 1,
    "name": "Paneer Tikka",
    "price": 180,
    "category": "Appetizer",
    "available": 1
  }
]
```

**Success status:** `200 OK`

### 3.2 Get Available Menu Items

**Endpoint:** `GET /api/menu/active`

Returns only menu items where `available = 1`.

**Success status:** `200 OK`

### 3.3 Add a Menu Item

**Endpoint:** `POST /api/menu`

Example request:

```json
{
  "name": "Masala Dosa",
  "price": 120,
  "category": "Main Course"
}
```

Example response:

```json
{
  "message": "Menu item added successfully"
}
```

**Success status:** `201 Created`

Validation rules:
- Name and category are required.
- Price must be a positive number.
- Boolean values are not accepted as prices.

**Error status:** `400 Bad Request` for invalid or missing required values.

### 3.4 Update Menu Availability

**Endpoint:** `PATCH /api/menu/1/availability`

Example request:

```json
{
  "available": false
}
```

Example response:

```json
{
  "message": "Availability updated successfully",
  "available": false
}
```

**Success status:** `200 OK`

Possible errors:
- `400` — Availability is missing or is not a boolean.
- `404` — Menu item not found.

## 4. Order APIs

### 4.1 Place an Order

**Endpoint:** `POST /api/orders`

Places a new order for a selected table.

Example request:

```json
{
  "table_number": 6,
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 1
    }
  ]
}
```

Example response:

```json
{
  "message": "Order placed successfully",
  "order_id": 16,
  "table_number": 6,
  "total": 180,
  "status": "Received"
}
```

**Success status:** `201 Created`

The backend calculates the total using the menu prices stored in the database. The table number is saved with the order and returned in the response.

Validation rules:
- The request must contain valid JSON.
- The `items` field must be a list containing at least one item.
- `table_number` must be a positive integer.
- Each item must have a valid positive integer menu item ID.
- Quantity must be an integer between 1 and 100.
- Duplicate menu item IDs are not allowed in one order.
- Unavailable or nonexistent menu items cannot be ordered.

Possible errors:
- `400` — Invalid JSON, missing order items, invalid table number or invalid order details.
- `500` — Database error while placing the order.

### 4.2 Get Order Details

**Endpoint:** `GET /api/orders/16`

Returns the details of a specific order, including its table number, items, quantities, prices, total and current status.

Example response:

```json
{
  "order_id": 16,
  "table_number": 6,
  "total": 180,
  "status": "Received",
  "items": [
    {
      "name": "Paneer Tikka",
      "quantity": 1,
      "price": 180,
      "subtotal": 180
    }
  ]
}
```

**Success status:** `200 OK`

Possible errors:
- `404` — Order not found.
- `500` — Unable to retrieve order details.

### 4.3 Get All Orders

**Endpoint:** `GET /api/orders`

Returns all orders, newest first, with their table numbers, items, totals and current statuses.

Example response:

```json
[
  {
    "order_id": 16,
    "table_number": 6,
    "total": 180,
    "status": "Received",
    "items": [
      {
        "name": "Paneer Tikka",
        "quantity": 1,
        "price": 180,
        "subtotal": 180
      }
    ]
  }
]
```

Older orders created before the table-number feature may have a `null` table number.

**Success status:** `200 OK`

**Error status:** `500` if orders cannot be retrieved.

This endpoint is used by the kitchen dashboard to display orders and their table numbers.

### 4.4 Update Order Status

**Endpoint:** `PATCH /api/orders/16/status`

This endpoint automatically advances the order to the next status. No request body is required.

Order status flow:

`Received → Cooking → Served`

Example response:

```json
{
  "message": "Order status updated successfully",
  "order_id": 16,
  "status": "Cooking"
}
```

**Success status:** `200 OK`

Possible errors:
- `400` — Order has already been served.
- `404` — Order not found.
- `500` — Database error while updating status.

## 5. HTTP Status Codes

| Status | Meaning |
|---|---|
| 200 | Request successful |
| 201 | Resource created successfully |
| 400 | Invalid request or business rule violation |
| 404 | Requested item or order not found |
| 500 | Server/database error |

## 6. Testing the APIs

The APIs can be tested using Postman, PowerShell or automated Pytest tests.

Example PowerShell command to retrieve the active menu:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/menu/active"
```

Example PowerShell command to place an order for Table 6:

```powershell
$body = @{
    table_number = 6
    items = @(
        @{
            menu_item_id = 1
            quantity = 1
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/api/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

The Flask backend must be running before these commands are executed.

## 7. Conclusion

The Kitchen Menu & Order Router API connects the customer ordering interface with the kitchen dashboard.

Customers can view available dishes, select a table number and place orders. Kitchen staff can view incoming orders, identify the associated table and move orders through the preparation stages.

The backend handles input validation, database operations, order totals and order status management.
