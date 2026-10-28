
import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:5000/api'

function App() {
  const [page, setPage] = useState('customer')
  const [menu, setMenu] = useState([])
  const [quantities, setQuantities] = useState({})
  const [tableNumber, setTableNumber] = useState('1')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [order, setOrder] = useState(null)
  const [orders, setOrders] = useState([])
  const [placingOrder, setPlacingOrder] = useState(false)
  const [updatingOrderId, setUpdatingOrderId] = useState(null)

  useEffect(() => {
    getMenu()
  }, [])

  useEffect(() => {
    if (page === 'kitchen') {
      getOrders()
    }
  }, [page])

  async function getMenu() {
    try {
      const response = await fetch(`${API_URL}/menu/active`)
      if (!response.ok) throw new Error('Failed to load menu')
      setMenu(await response.json())
    } catch (error) {
      setError('Could not load menu. Please check the backend.')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  async function getOrders() {
    try {
      setError('')
      const response = await fetch(`${API_URL}/orders`)
      if (!response.ok) throw new Error('Failed to load orders')
      setOrders(await response.json())
    } catch (error) {
      setError('Could not load orders. Please check the backend.')
      console.error(error)
    }
  }

  function changeQuantity(itemId, change) {
    const currentQuantity = quantities[itemId] || 0
    const newQuantity = currentQuantity + change

    if (newQuantity < 0 || newQuantity > 100) return

    setQuantities((previous) => ({
      ...previous,
      [itemId]: newQuantity,
    }))

    setError('')
    setMessage('')
    setOrder(null)
  }

  const itemCount = menu.reduce(
    (sum, item) => sum + (quantities[item.id] || 0),
    0
  )

  const total = menu.reduce(
    (sum, item) =>
      sum + Number(item.price) * (quantities[item.id] || 0),
    0
  )

  async function placeOrder() {
    const items = menu
      .filter((item) => (quantities[item.id] || 0) > 0)
      .map((item) => ({
        menu_item_id: item.id,
        quantity: quantities[item.id],
      }))

    if (items.length === 0) {
      setError('Please select at least one item.')
      return
    }

    try {
      setError('')
      setMessage('')
      setOrder(null)
      setPlacingOrder(true)

      const response = await fetch(`${API_URL}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table_number: Number(tableNumber),
          items,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Could not place order.')
      }

      setOrder(data)
      setMessage('Order placed successfully!')
      setQuantities({})
    } catch (error) {
      setError(error.message || 'Could not connect to the backend.')
    } finally {
      setPlacingOrder(false)
    }
  }

  async function updateOrderStatus(orderId) {
    try {
      setError('')
      setUpdatingOrderId(orderId)

      const response = await fetch(
        `${API_URL}/orders/${orderId}/status`,
        { method: 'PATCH' }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Could not update status.')
      }

      setOrders((previous) =>
        previous.map((item) =>
          item.order_id === orderId
            ? { ...item, status: data.status }
            : item
        )
      )

      if (order?.order_id === orderId) {
        setOrder((previous) => ({ ...previous, status: data.status }))
      }

      setMessage(`Order #${orderId} is now ${data.status}.`)
    } catch (error) {
      setError(error.message || 'Could not update order status.')
    } finally {
      setUpdatingOrderId(null)
    }
  }

  function renderOrderCard(item) {
    return (
      <article className="kitchen-order-card" key={item.order_id}>
        <div className="order-card-heading">
          <h3>
            Order #{item.order_id} — Table{' '}
            {item.table_number ?? 'Not assigned'}
          </h3>

          <span className={`status-label status-${item.status.toLowerCase()}`}>
            {item.status}
          </span>
        </div>

        <ul className="kitchen-order-items">
          {item.items.map((food, index) => (
            <li key={`${food.name}-${index}`}>
              <span>
                {food.name} × {food.quantity}
              </span>
              <span>₹{Number(food.subtotal).toFixed(2)}</span>
            </li>
          ))}
        </ul>

        <div className="kitchen-order-total">
          Total: ₹{Number(item.total).toFixed(2)}
        </div>

        {item.status !== 'Served' && (
          <button
            type="button"
            className="order-status-button"
            onClick={() => updateOrderStatus(item.order_id)}
            disabled={updatingOrderId === item.order_id}
          >
            {updatingOrderId === item.order_id
              ? 'Updating...'
              : item.status === 'Received'
                ? 'Start Cooking'
                : 'Mark as Served'}
          </button>
        )}
      </article>
    )
  }

  return (
    <div className="app">
      <header>
        <h1>Kitchen Router</h1>
        <p>On-Demand Kitchen Menu &amp; Order Router</p>

        <nav className="app-navigation">
          <button
            type="button"
            className={page === 'customer' ? 'nav-active' : ''}
            onClick={() => {
              setPage('customer')
              setError('')
            }}
          >
            Customer Menu
          </button>

          <button
            type="button"
            className={page === 'kitchen' ? 'nav-active' : ''}
            onClick={() => {
              setPage('kitchen')
              setError('')
            }}
          >
            Kitchen Dashboard
          </button>
        </nav>
      </header>

      <main>
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        {page === 'customer' ? (
          <>
            <h2>Available Menu</h2>

            <div className="table-selector">
              <label htmlFor="table-number">Select Table Number:</label>
              <select
                id="table-number"
                value={tableNumber}
                onChange={(event) => setTableNumber(event.target.value)}
              >
                {Array.from({ length: 20 }, (_, index) => index + 1).map(
                  (table) => (
                    <option key={table} value={table}>
                      Table {table}
                    </option>
                  )
                )}
              </select>
            </div>

            {loading && <p>Loading menu...</p>}

            {!loading && menu.length === 0 && !error && (
              <p>No menu items available.</p>
            )}

            <div className="menu-list">
              {menu.map((item) => (
                <div className="menu-card" key={item.id}>
                  <h3>{item.name}</h3>
                  <p>Category: {item.category}</p>
                  <p>Price: ₹{Number(item.price).toFixed(2)}</p>

                  <div className="quantity-control">
                    <button
                      type="button"
                      onClick={() => changeQuantity(item.id, -1)}
                      disabled={!quantities[item.id]}
                    >
                      −
                    </button>

                    <span>{quantities[item.id] || 0}</span>

                    <button
                      type="button"
                      onClick={() => changeQuantity(item.id, 1)}
                      disabled={(quantities[item.id] || 0) >= 100}
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <section className="order-summary">
              <h2>Order Summary</h2>
              <p>Items selected: {itemCount}</p>
              <h3>Total: ₹{total.toFixed(2)}</h3>

              <button
                type="button"
                onClick={placeOrder}
                disabled={loading || itemCount === 0 || placingOrder}
              >
                {placingOrder ? 'Placing Order...' : 'Place Order'}
              </button>
            </section>

            {order && (
              <section className="order-result">
                <h2>Order Placed Successfully!</h2>

                <div className="order-detail-row">
                  <span>Order ID</span>
                  <strong>#{order.order_id}</strong>
                </div>

                <div className="order-detail-row">
                  <span>Table Number</span>
                  <strong>Table {order.table_number}</strong>
                </div>

                <div className="order-detail-row">
                  <span>Total Amount</span>
                  <strong>₹{Number(order.total).toFixed(2)}</strong>
                </div>

                <div className="order-detail-row">
                  <span>Order Status</span>
                  <strong>{order.status}</strong>
                </div>

                <p>
                  Use the Kitchen Dashboard to manage this order&apos;s status.
                </p>
              </section>
            )}
          </>
        ) : (
          <section className="kitchen-dashboard">
            <div className="dashboard-heading">
              <div>
                <h2>Kitchen Dashboard</h2>
                <p>Track incoming orders and prepare them for serving.</p>
              </div>

              <button type="button" onClick={getOrders}>
                Refresh Orders
              </button>
            </div>

            <div className="kitchen-columns">
              {['Received', 'Cooking', 'Served'].map((status) => {
                const statusOrders = orders.filter(
                  (item) => item.status === status
                )

                return (
                  <section className="kitchen-column" key={status}>
                    <h3>
                      {status} ({statusOrders.length})
                    </h3>

                    {statusOrders.length === 0 ? (
                      <p className="empty-orders">
                        No {status.toLowerCase()} orders.
                      </p>
                    ) : (
                      statusOrders.map(renderOrderCard)
                    )}
                  </section>
                )
              })}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
