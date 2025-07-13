#!/usr/bin/env python3

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    # Write heartbeat message
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(log_message)

    # Optional GraphQL hello check
    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=True, retries=2)
        client = Client(transport=transport, fetch_schema_from_transport=False)

        query = gql("{ hello }")
        result = client.execute(query)

        with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
            log_file.write(f"{timestamp} GraphQL hello response: {result.get('hello')}\n")

    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
            log_file.write(f"{timestamp} GraphQL hello check failed: {str(e)}\n")

def update_low_stock():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_path = "/tmp/low_stock_updates_log.txt"

    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=True, retries=2)
        client = Client(transport=transport, fetch_schema_from_transport=False)

        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    updatedProducts
                    message
                }
            }
        """)

        result = client.execute(mutation)
        updated_products = result["updateLowStockProducts"]["updatedProducts"]

        with open(log_file_path, "a") as log_file:
            log_file.write(f"{timestamp} - {result['updateLowStockProducts']['message']}\n")
            for product in updated_products:
                log_file.write(f"{timestamp} - {product}\n")

    except Exception as e:
        with open(log_file_path, "a") as log_file:
            log_file.write(f"{timestamp} - Low stock update failed: {str(e)}\n")
