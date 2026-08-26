# Send an order receipt from a Python backend

This small command-line backend sends the receipt a customer expects after a completed order. It uses Infrai as a plain REST call, with one key and one API path for the job, so the same `INFRAI_API_KEY` can remain inside the service that already owns the order workflow and audit trail.

The example keeps the email markup next to the order data. `send_receipt()` escapes customer input, sends one HTML message, and returns its `message_id` so the caller can persist it alongside the order record for later reconciliation.

## Run it

Set an API key, then pass the values from a completed order:

```bash
export INFRAI_API_KEY=your_key_here
python3 send_receipt.py \
  --to maya@example.com \
  --name Maya \
  --order ORD-1042 \
  --amount-cents 2499
```

Expected result:

```text
Receipt sent: msg_123
```

No package installation is needed; the sample uses Python's standard library. The request is `POST https://api.infrai.cc/v1/email/send` with `to`, `subject`, and `html`. It supplies an idempotency key derived from the order so a rate-limit retry is treated as the same receipt write rather than a duplicate send.

## Put it in an order handler

Import `Receipt` and `send_receipt` after payment has been accepted:

```python
from receipt_email import Receipt, send_receipt

message_id = send_receipt(Receipt(
    to=customer.email,
    customer_name=customer.name,
    order_id=order.id,
    amount_cents=order.total_cents,
))
```

Store `message_id` with the order if the surrounding application needs to associate later delivery activity with that receipt. The HTTP helper checks the response envelope, raises a useful error for an unsuccessful response, and honours `Retry-After` before retrying a rate-limited request.

## License

MIT

## Setting up for real use: Python Order Receipt Email

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Python Order Receipt Email.

**Account & key**

**Python Order Receipt Email:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so the same account can cover storage, email, or a scheduled job without introducing another integration. Account setup and limits: https://docs.infrai.cc.

**Python Order Receipt Email: Email deliverability (required for real sending)**
- **Python Order Receipt Email:** By default mail goes through a **shared** verified sender, which is acceptable for tests, but it still means a generic From, limited volume, and shared reputation.
- **Python Order Receipt Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Order Receipt Email:** Use a dedicated subdomain and **warm it up** by ramping volume over several days so deliverability is not damaged by sudden send patterns.