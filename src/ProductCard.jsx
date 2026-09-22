function ProductCard({ product, cartQuantity, onAdd }) {
  return (
    <article className="card">
      <img src={product.thumbnail} alt={product.title} />
      <h3>{product.title}</h3>
      <p className="price">${product.price.toFixed(2)}</p>
      <p className="meta">
        Rating: {product.rating.toFixed(1)} · Stock: {product.stock}
      </p>
      <button className="add-btn" onClick={onAdd} disabled={cartQuantity >= product.stock}>
        {cartQuantity >= product.stock ? 'Stock máximo' : 'Agregar'}
      </button>
    </article>
  )
}

export default ProductCard
