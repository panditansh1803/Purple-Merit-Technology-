# Release Notes — Smart Payment Routing v2.0

**Release Date:** 2026-03-31  
**Version:** 2.0.0-stable  
**Team:** Payments Platform  
**Release Manager:** Anaya Sharma  

---

## Feature Description

Smart Payment Routing v2.0 introduces an AI-driven routing engine that dynamically selects the optimal payment gateway (Stripe, Razorpay, PayU, Cashfree) based on real-time success rate signals, latency metrics, and transaction type. The goal is to increase overall payment success rates by 2–3% and reduce checkout friction.

### Key Changes
- **Dynamic gateway selection** replacing the static round-robin approach
- **Real-time fallback logic** — if a gateway's success rate drops below 94%, traffic is automatically rerouted
- **New ML model** for transaction classification (UPI / card / wallet)
- **Database schema migration** for routing decision logs (new `routing_events` table)
- New dependency: `payment-router-sdk v3.1.2` (third-party)

---

## Success Criteria (Go/No-Go Thresholds)

| Metric | Target | Minimum Acceptable | Roll Back If |
|---|---|---|---|
| Payment Success Rate | ≥ 98.5% | ≥ 96.0% | < 92.0% |
| API Latency p95 | ≤ 300ms | ≤ 500ms | > 800ms |
| Crash Rate | ≤ 0.5% | ≤ 1.0% | > 2.0% |
| D1 Retention | ≥ 55% | ≥ 50% | < 45% |
| Support Tickets/day | ≤ 100 | ≤ 180 | > 300 |

---

## Known Risks & Issues at Launch

1. **[HIGH] Third-party SDK cold-start latency** — `payment-router-sdk v3.1.2` shows 40–60ms additional latency during the first 10 minutes of a new deployment. Expected to stabilize; monitored.

2. **[MEDIUM] DB migration lock risk** — The `routing_events` table migration may cause read locks on the transactions table for ~30 seconds during peak traffic. Mitigation: scheduled for off-peak (02:00 IST).

3. **[MEDIUM] ML model confidence in low-data regions** — The routing ML model has lower confidence for transactions < ₹500 (only 8% of training data). May show higher failure rates for micro-transactions.

4. **[LOW] Cache invalidation edge case** — Under specific race conditions, the gateway health cache may serve stale data for up to 90 seconds. Fix scheduled for v2.0.1.

5. **[LOW] iOS Safari compatibility** — The new payment confirmation modal has a rendering glitch on iOS Safari 16.x. CSS fix in progress.

---

## Rollback Plan

1. Flip feature flag `payment_routing_v2` to `false` in ConfigMap
2. Redeploy previous image: `payments-service:v1.8.5`
3. Run DB rollback script: `scripts/rollback_routing_events.sql`
4. Verify payment success rate recovers within 15 minutes
5. Notify on-call engineer and post incident report within 24 hours

---

## Dependencies

- `payment-router-sdk v3.1.2` (third-party, Payments Inc.)
- `ml-routing-model v0.4.1` (internal ML team)
- PostgreSQL 14.x (routing_events table migration)
- Feature flag service: `flagsmith` (env: `payment_routing_v2`)
