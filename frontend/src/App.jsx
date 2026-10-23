
import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [menu, setMenu] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default App
