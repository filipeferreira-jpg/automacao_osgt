import requests
import json

response = requests.get('http://seu-n8n.com/webhook/phinia-query?id=9')
data = response.json()

for invoice in data:
    print(f"\n=== Invoice: {invoice['invoice_number']} ===\n")

    # Converter string JSON para array
    items = json.loads(invoice['items'])

    print(f"Total de itens: {len(items)}\n")

    for item in items:
        print(f"Part Number: {item['part_number']}")
        print(f"Quantidade: {item['quantity']}")
        print(f"Custom Order: {item['custom_order_nro']}")
        print(f"Preço: {item['net_price']}")
        print(f"Total: {item['total_value']}")
        print("-" * 40)
