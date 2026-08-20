# Security and tenant enforcement

Status: **Phase 1 implementation contract**

## Identity and onboarding

- Authentication is required by default for ASP.NET controllers.
- The only anonymous backend routes are health checks, rate-limited contact and
  login/invitation acceptance, plus the development-only platform bootstrap.
- Merchant self-registration is disabled. A platform administrator creates an
  Account, its Store and the Store's one-to-one Tenant partition atomically,
  then issues an expiring single-use invitation.
- Merchant login requires both the tenant claim and an active account
  membership for the Store mapped to that tenant.
- Passwords use ASP.NET Core Identity hashing. Legacy PBKDF2-SHA256 values are
  accepted once and upgraded after a successful login.
- Access tokens are short-lived, contain a unique token ID and are invalidated
  through the persisted token version after password or session changes.
- Login and public writes are rate-limited; repeated login failure triggers a
  timed lockout.
- API-key secrets are hashed at rest. The full value is returned only by the
  regeneration response and is never returned by settings reads.

## Tenant boundary

The ownership chain is:

```text
Account -> Store -> Tenant -> tenant-owned records
```

Tenant context comes from a verified token claim. An authenticated platform
administrator may select an existing tenant with `X-Tavaura-Tenant` for
support/administration. Anonymous and merchant-supplied selection headers do
not override identity.

Tenant enforcement has three layers:

1. EF Core global query filters default-deny tenant-owned tables when no tenant
   context exists.
2. Composite `(TenantId, Id)` keys and foreign keys prevent cross-tenant links
   across the garment, asset-version, render-job and render-result chain.
3. PostgreSQL row-level-security policies enforce the current tenant session
   variable, with explicit platform and worker system contexts.

Production must use a dedicated application database role that does not own the
tables and does not have `BYPASSRLS`; PostgreSQL table owners bypass ordinary
RLS unless `FORCE ROW LEVEL SECURITY` is used. Migration/owner credentials must
remain separate from API and worker runtime credentials.

## Remote image policy

The worker has one remote-image intake implementation for ingestion and mock
rendering. It:

- permits only HTTP/HTTPS on standard ports;
- rejects credentials in URLs;
- resolves every redirect hop and rejects any non-public DNS answer;
- connects to the validated address while preserving HTTPS hostname checking;
- limits redirects, connection/read time, declared and streamed bytes;
- accepts only enabled JPEG, PNG and WebP MIME types;
- verifies MIME/format agreement and bounded dimensions/pixel count;
- logs only the origin, never query strings or URL credentials.

The .NET API performs no remote media downloads. New .NET download behavior is
prohibited until it implements this same contract or delegates to the worker.
Production infrastructure must also deny worker access to instance metadata,
private service ranges and control-plane networks as a defense-in-depth egress
rule.
