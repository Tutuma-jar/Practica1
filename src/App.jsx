import { useState, useEffect } from 'react'
import ProductCard from './ProductCard'
import Cart from './Cart'
import { getDiscountedPrice } from './pricing'
import './App.css'

const API_URL = 'https://dummyjson.com/products'
const FALLBACK_CATEGORIES = ['beauty', 'fragrances', 'furniture', 'groceries']

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCart, setShowCart] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    setLoading(true)
    setError('')
    const normalizedSearch = search.trim()
    const url = normalizedSearch
      ? `${API_URL}/search?q=${encodeURIComponent(normalizedSearch)}&limit=0`
      : `${API_URL}?limit=0`

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Error HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setProducts(data.products)
      })
      .catch((requestError) => {
        if (requestError.name === 'AbortError') return

        setProducts([])
        setError('No se pudieron cargar los productos. Inténtalo de nuevo.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [search])

  useEffect(() => {
    const controller = new AbortController()

    fetch(`${API_URL}/category-list`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Error HTTP ${res.status}`)
        return res.json()
      })
      .then(setCategories)
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') {
          setCategories(FALLBACK_CATEGORIES)
        }
      })

    return () => controller.abort()
  }, [])

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
      currentCart.flatMap((item) => {
        if (item.id !== id) return [item]

        const quantity = Math.min(item.stock, Math.max(0, item.quantity + delta))
        return quantity === 0 ? [] : [{ ...item, quantity }]
      })
    )
  }

  function removeFromCart(id) {
    setCart((currentCart) => currentCart.filter((item) => item.id !== id))
  }

  function remainingStock(item) {
    const current = products.find((p) => p.id === item.id)
    const quantity = cart.find((c) => c.id === item.id)?.quantity ?? 0
    const stock = current ? current.stock : item.stock
    return Math.max(0, stock - quantity)
  }

  function checkout() {
    alert(`Compra realizada. Total: $${total.toFixed(2)}`)
    setProducts((currentProducts) =>
      currentProducts.map((p) => {
        const bought = cart.find((item) => item.id === p.id)?.quantity ?? 0
        return bought > 0 ? { ...p, stock: Math.max(0, p.stock - bought) } : p
      })
    )
    setCart([])
  }

  const total = cart.reduce(
    (sum, item) => sum + getDiscountedPrice(item) * item.quantity,
    0
  )
  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0)

  const visibleProducts = products.filter(
    (product) => category === 'all' || product.category === category
  )

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
          {categories.map((c) => (
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
              stock={remainingStock(p)}
              onAdd={() => addToCart(p)}
            />
          ))}
        </div>
      </main>

      {showCart && (
        <Cart
          items={cart.map((item) => ({ ...item, remaining: remainingStock(item) }))}
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
