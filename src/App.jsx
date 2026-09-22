import { useState, useEffect } from 'react'
import ProductCard from './ProductCard'
import Cart from './Cart'
import './App.css'

const API_URL = 'https://dummyjson.com/products'
const CATEGORIES = ['beauty', 'fragrances', 'furniture', 'groceries']
const MAX_SEARCH_LENGTH = 50
const CART_STORAGE_KEY = 'tienda-cart'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(true)
  const [showCart, setShowCart] = useState(false)

  useEffect(() => {
    try {
      const savedCart = JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '[]')
      if (Array.isArray(savedCart)) {
        setCart(savedCart)
      }
    } catch (error) {
      console.error('No se pudo cargar el carrito:', error)
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart))
    } catch (error) {
      console.error('No se pudo guardar el carrito:', error)
    }
  }, [cart])

  useEffect(() => {
    setLoading(true)
    const url = search
      ? `${API_URL}/search?q=${encodeURIComponent(search)}`
      : `${API_URL}?limit=30`

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setProducts(data.products)
        setLoading(false)
      })
  }, [search])

  function addToCart(product) {
    setCart((currentCart) => [...currentCart, { ...product, quantity: 1 }])
  }

  function changeQty(index, delta) {
    setCart((currentCart) =>
      currentCart.map((item, i) =>
        i === index ? { ...item, quantity: item.quantity + delta } : item
      )
    )
  }

  function removeFromCart(item) {
    setCart((currentCart) => currentCart.filter((c) => c.category !== item.category))
  }

  function checkout() {
    alert(`Compra realizada. Total: $${total.toFixed(2)}`)
    setCart([])
  }

  const total = cart.reduce(
    (sum, item) => sum + (item.price - item.discountPercentage) * item.quantity,
    0
  )

  const visibleProducts = products
    .filter((p) => category === 'all' || p.category === category)
    .filter((p) => p.title.includes(search))

  return (
    <div className="app">
      <header className="header">
        <h1>Tienda Tech</h1>
        <input
          className="search"
          type="search"
          aria-label="Buscar productos"
          placeholder="Buscar..."
          maxLength={MAX_SEARCH_LENGTH}
          value={search}
          onChange={(e) => setSearch(e.target.value.slice(0, MAX_SEARCH_LENGTH))}
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
          Carrito ({cart.length})
        </button>
      </header>

      <main>
        {loading && <p className="loading">Cargando...</p>}

        {!loading && visibleProducts.length === 0 && <p>Sin resultados.</p>}

        <div className="grid">
          {visibleProducts.map((p) => (
            <ProductCard key={p.id} product={p} onAdd={() => addToCart(p)} />
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
        />
      )}
    </div>
  )
}

export default App
