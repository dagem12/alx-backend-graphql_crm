import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql_crm.settings")
django.setup()

from crm.models import Customer, Product, Order
from django.utils import timezone

# Create sample customers
customers = [
    Customer(name="Alice", email="alice@example.com", phone="+1234567890"),
    Customer(name="Bob", email="bob@example.com", phone="123-456-7890"),
    Customer(name="Carol", email="carol@example.com")
]
Customer.objects.bulk_create(customers)

# Create sample products
products = [
    Product(name="Laptop", price=999.99, stock=10),
    Product(name="Phone", price=499.99, stock=25),
    Product(name="Headphones", price=99.99, stock=50)
]
Product.objects.bulk_create(products)

# Create one sample order
order = Order.objects.create(
    customer=Customer.objects.get(email="alice@example.com"),
    total_amount=999.99 + 99.99,
    order_date=timezone.now()
)
order.products.set(Product.objects.filter(name__in=["Laptop", "Headphones"]))

print("Seed data inserted.")

