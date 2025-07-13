from itertools import product
import re
import graphene
from graphene_django.types import DjangoObjectType
from crm.models import Customer, Order, Product
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone

from decimal import Decimal


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("customer_id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("product_id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("order_id", "customer", "products", "total_amount", "order_date")

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class CustomerProduct(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False)

class CustomerOrder(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    customer = graphene.Field(CustomerType)

    def mutate(self, info, input):
        name = input.name
        email = input.email
        phone = input.phone

        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(success=False, message="Email already exists", customer=None)

        if phone:
            pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
            if not re.match(pattern, phone):
                return CreateCustomer(success=False, message="Invalid phone format", customer=None)

        customer = Customer.objects.create(name=name, email=email, phone=phone or "")
        return CreateCustomer(success=True, message="Customer created", customer=customer)
    
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created_customers = []
        errors = []

        for customer in input:
            if Customer.objects.filter(email=customer.email).exists():
                errors.append(f"{customer.email} already exists.")
                continue

            if customer.phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', customer.phone):
                errors.append(f"{customer.phone} is invalid.")
                continue

            created_customers.append(Customer.objects.create(
                name=customer.name,
                email=customer.email,
                phone=customer.phone or ""
            ))

        return BulkCreateCustomers(customers=created_customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CustomerProduct(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        name = input.name
        price = Decimal(str(input.price))
        stock = input.stock

        if price <= 0:
            return CreateProduct(success=False, message="Price must be positive", product=None)

        if stock < 0:
            return CreateProduct(success=False, message="Stock cannot be negative", product=None)

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(success=True, message="Product created", product=product)
    
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CustomerOrder(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        customer_id = input.customer_id
        product_ids = input.product_ids
        order_date = input.order_date

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, message="Invalid customer ID", order=None)

        products = Product.objects.filter(pk__in=product_ids)
        if not products.exists():
            return CreateOrder(success=False, message="No valid products found", order=None)

        total = sum(p.price for p in products)
        order = Order.objects.create(
            customer=customer,
            order_date=order_date or timezone.now(),
            total_amount=total
        )
        order.products.set(products)

        return CreateOrder(success=True, message="Order created", order=order)
    

class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(graphene.String)
    message = graphene.String()

    def mutate(self, info):
        products = Product.objects.filter(stock__lt=10)
        updated_names = []

        for product in products:
            product.stock += 10
            product.save()
            updated_names.append(f"{product.name} (New Stock: {product.stock})")

        return UpdateLowStockProducts(
            updated_products=updated_names,
            message="Low-stock products restocked successfully!"
        )
    

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()

