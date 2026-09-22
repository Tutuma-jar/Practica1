function ProductCard({ product, stock, onAdd }) {
  const soldOut = stock <= 0

  return (
    <article className="card">
      <img src={product.thumbnail} alt={product.title} />
      <h3>{product.title}</h3>
      <p className="price">${product.price.toFixed(2)}</p>
      <p className="meta">
        Rating: {product.rating.toFixed(1)} · Stock: {stock}
      </p>
      <button className="add-btn" onClick={onAdd} disabled={soldOut}>
        {soldOut ? 'Sin stock' : 'Agregar'}
      </button>
    </article>
  )
}

export default ProductCard
