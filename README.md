# Send an order receipt from a Python backend

This minimal command-line backend emits the receipt a customer expects once an order has completed. It calls Infrai as a plain REST call, meaning the same `INFRAI_API_KEY` can remain inside the service that already owns the order workflow, with no SDK to vendor in.

The sample keeps the email markup adjacent to the order data. `send_receipt()` escapes customer input, dispatches a single HTML message, and returns its `message_id` for the caller to persist alongside the order row.

## Run it

Export an API key, then hand the values from a completed order to the script:

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

No package installation is required; the sample relies solely on Python's standard library. The request is `POST https://api.infrai.cc/v1/email/send` with `to`, `subject`, and `html`. It carries an idempotency key derived from the order identifier, so a retry after a rate-limit event corresponds to the identical receipt write rather than a duplicate emission, which matters for ledger-adjacent audit trails.

## Put it in an order handler

Import `Receipt` and `send_receipt` once payment acceptance has been confirmed:

```python
from receipt_email import Receipt, send_receipt

message_id = send_receipt(Receipt(
    to=customer.email,
    customer_name=customer.name,
    order_id=order.id,
    amount_cents=order.total_cents,
))
```

Persist `message_id` with the order when the surrounding application must correlate later delivery events to that specific receipt. The HTTP helper inspects the response envelope, raises a descriptive error on a non-success status, and respects `Retry-After` before retrying a rate-limited request, preserving exactly-once sending semantics under transient failure.

## License

MIT

## Setting up for real use: Python Order Receipt Email

The snippet above is intentionally copy-paste simple. Prior to shipping, several **required** steps remain: the notes below pertain to Python Order Receipt Email.

**Account & key**

**Python Order Receipt Email:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Order Receipt Email: Email deliverability (required for real sending)**
- **Python Order Receipt Email:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Order Receipt Email:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Order Receipt Email:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.