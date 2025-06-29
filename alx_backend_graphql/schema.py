import graphene
from graphene_django import DjangoObjectType
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from crm.models import Customer, Product, Order

# Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Validate email uniqueness
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email already exists")

        # Validate phone format if provided
        if input.phone:
            phone_validator = RegexValidator(
                regex=r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$',
                message="Phone number must be in format +1234567890 or 123-456-7890"
            )
            try:
                phone_validator(input.phone)
            except ValidationError as e:
                raise Exception(f"Invalid phone number: {e.message}")

        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for idx, cust_input in enumerate(input):
                try:
                    if Customer.objects.filter(email=cust_input.email).exists():
                        raise Exception(f"Email '{cust_input.email}' already exists")

                    if cust_input.phone:
                        phone_validator = RegexValidator(
                            regex=r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$',
                            message="Phone number must be in format +1234567890 or 123-456-7890"
                        )
                        phone_validator(cust_input.phone)

                    customer = Customer(
                        name=cust_input.name,
                        email=cust_input.email,
                        phone=cust_input.phone
                    )
                    customer.full_clean()
                    customer.save()
                    created_customers.append(customer)
                except Exception as e:
                    errors.append(f"Record {idx + 1}: {str(e)}")
            # partial success: continue creating valid entries

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        if input.price <= 0:
            raise Exception("Price must be a positive number")

        if input.stock is not None and input.stock < 0:
            raise Exception("Stock must be zero or a positive integer")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock if input.stock is not None else 0
        )
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        # Validate customer exists
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        # Validate products exist and at least one product
        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            raise Exception("At least one valid product must be selected")
        if products.count() != len(product_ids):
            raise Exception("One or more product IDs are invalid")

        # Calculate total_amount accurately
        total_amount = sum([product.price for product in products])

        order = Order.objects.create(
            customer=customer,
            order_date=order_date or timezone.now(),
            total_amount=total_amount
        )
        order.products.set(products)
        return CreateOrder(order=order)


class Query(graphene.ObjectType):
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

