export function getDiscountedPrice(product) {
  return product.price * (1 - product.discountPercentage / 100)
}
