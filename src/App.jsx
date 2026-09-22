import { useState, useEffect } from 'react'
import ProductCard from './ProductCard'
import Cart from './Cart'
import './App.css'

const API_URL = 'https://dummyjson.com/products'
const CATEGORIES = ['beauty', 'fragrances', 'furniture', 'groceries']

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCart, setShowCart] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError('')
    const url = search
      ? `${API_URL}/search?q=${encodeURIComponent(search)}`
      : `${API_URL}?limit=30`

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Error HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setProducts(data.products)
      })
      .catch(() => {
        setProducts([])
        setError('No se pudieron cargar los productos. Inténtalo de nuevo.')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [search])

  function addToCart(product) {
    setCart((currentCart) => {
      const existingItem = currentCart.find((item) => item.id === product.id)

      if (existingItem) {
        return currentCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: Math.min(item.stock, item.quantity + 1) }
            : item
        )
      }

      if (product.stock < 1) return currentCart

      return [...currentCart, { ...product, quantity: 1 }]
    })
  }

  function changeQty(id, delta) {
    setCart((currentCart) =>
      currentCart.map((item) =>
        item.id === id
          ? {
              ...item,
              quantity: Math.min(item.stock, Math.max(1, item.quantity + delta)),
            }
          : item
      )
    )
  }

  function removeFromCart(id) {
    setCart((currentCart) => currentCart.filter((item) => item.id !== id))
  }

  function checkout() {
    alert(`Compra realizada. Total: $${total.toFixed(2)}`)
    setCart([])
  }

  const total = cart.reduce(
    (sum, item) =>
      sum + item.price * (1 - item.discountPercentage / 100) * item.quantity,
    0
  )
  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0)

  const visibleProducts = products
    .filter((p) => category === 'all' || p.category === category)
    .filter((p) => p.title.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="app">
      <header className="header">
        <h1>Tienda Tech</h1>
        <input
          className="search"
          type="search"
          aria-label="Buscar productos"
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label="Filtrar por categoría"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="all">Todas</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <button className="cart-btn" onClick={() => setShowCart(!showCart)}>
          Carrito ({cartItemCount})
        </button>
      </header>

      <main>
        {loading && <p className="loading">Cargando...</p>}

        {error && <p role="alert">{error}</p>}

        {!loading && !error && visibleProducts.length === 0 && <p>Sin resultados.</p>}

        <div className="grid">
          {visibleProducts.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              cartQuantity={cart.find((item) => item.id === p.id)?.quantity ?? 0}
              onAdd={() => addToCart(p)}
            />
          ))}
        </div>
      </main>

      {showCart && (
        <Cart
          items={cart}
          total={total}
          onQty={changeQty}
          onRemove={removeFromCart}
          onCheckout={checkout}
          onClose={() => setShowCart(false)}
        />
      )}
    </div>
  )
}

export default App
