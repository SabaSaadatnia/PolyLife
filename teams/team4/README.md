# PolyLife Team 4 Backend

Team 4 implements the following services:

- Product store and hierarchical categories
- Sports supplement information
- Redis-based shopping cart
- Discount codes
- Mock checkout and payment
- Orders and digital invoices

## Architecture

```text
Client
  ↓
Team 4 Nginx Gateway
  ↓ authentication verification
Core Service
  ↓ trusted user headers
Team 4 Django Backend
  ↓
PostgreSQL and Redis