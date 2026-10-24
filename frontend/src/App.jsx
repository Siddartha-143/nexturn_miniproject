
import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [menu, setMenu] = useState([])
  const [quantities, setQuantities] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [order, setOrder] = useState(null)
  const [placingOrder, setPlacingOrder] = useState(false)

  useEffect(() => {
    getMenu()
  }, [])

  async function getMenu() {
    try {
      const response = await fetch(
        'http://127.0.0.1:5000/api/menu/active'
      )

      if (!response.ok) {
        throw new Error('Failed to load menu')
      }

      const data = await response.json()
      setMenu(data)
    } catch (error) {
      setError('Could not load menu. Please check the backend.')
      console.log(error)
    } finally {
      setLoading(false)
    }
  }

  function changeQuantity(itemId, change) {
    const currentQuantity = quantities[itemId] || 0
    const newQuantity = currentQuantity + change

    if (newQuantity < 0) {
      return
    }

    setQuantities((previousQuantities) => ({
      ...previousQuantities,
      [itemId]: newQuantity,
    }))

    setError('')
    setMessage('')
    setOrder(null)
  }

  let total = 0
  let itemCount = 0

  for (const item of menu) {
    const quantity = quantities[item.id] || 0

    total = total + Number(item.price) * quantity
    itemCount = itemCount + quantity
  }

  async function placeOrder() {
    const items = []

    for (const item of menu) {
      const quantity = quantities[item.id] || 0

      if (quantity > 0) {
        items.push({
          menu_item_id: item.id,
          quantity: quantity,
        })
      }
    }

    if (items.length === 0) {
      setError('Please select at least one item.')
      return
    }

    try {
      setError('')
      setMessage('')
      setOrder(null)
      setPlacingOrder(true)

      const response = await fetch(
        'http://127.0.0.1:5000/api/orders',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ items }),
        }
      )

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

  return (
    <div className="app">
      <header>
        <h1>Kitchen Router</h1>
        <p>On-Demand Kitchen Menu & Order Router</p>
      </header>

      <main>
        <h2>Available Menu</h2>

        {loading && <p>Loading menu...</p>}

        {error && <p className="error">{error}</p>}

        {!loading && !error && menu.length === 0 && (
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
                  -
                </button>

                <span>{quantities[item.id] || 0}</span>

                <button
                  type="button"
                  onClick={() => changeQuantity(item.id, 1)}
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

        {message && <p className="success">{message}</p>}

        {order && (
          <section className="order-result">
            <h2>Order Details</h2>
            <p>
              Order ID: {order.order_id ?? order.id ?? 'Created'}
            </p>
            <p>
              Total: ₹
              {Number(order.total ?? 0).toFixed(2)}
            </p>
            <p>Status: {order.status || 'Received'}</p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
