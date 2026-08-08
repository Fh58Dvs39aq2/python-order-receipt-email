"""A command-line order confirmation email example."""

import argparse

from receipt_email import Receipt, send_receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Send an order receipt email")
    parser.add_argument("--to", required=True, help="Customer email address")
    parser.add_argument("--name", required=True, help="Customer name")
    parser.add_argument("--order", required=True, help="Completed order ID")
    parser.add_argument("--amount-cents", required=True, type=int, help="Paid amount in cents")
    args = parser.parse_args()

    message_id = send_receipt(
        Receipt(
            to=args.to,
            customer_name=args.name,
            order_id=args.order,
            amount_cents=args.amount_cents,
        )
    )
    print(f"Receipt sent: {message_id}")


if __name__ == "__main__":
    main()
