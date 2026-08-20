# ADR-0006: Tenant and Merchant Ownership Boundary

Status: **Accepted**

Date: **2026-08-20**

## Context

Most current domain records use `TenantId`, while newer Account, Store and
membership entities are not fully connected. Tenant selection can also fall
back to request headers, and isolation relies on manually repeated predicates.

## Decision

For the migration-safe MVP:

- Account represents the merchant organization and billing owner.
- Account owns one or more Stores.
- Each Store maps one-to-one to an existing Tenant security partition.
- Existing `TenantId` columns remain the immediate data boundary.
- User membership is validated before a tenant-scoped merchant session is issued.
- Storefront sessions are short-lived and scoped to tenant, product and origin.

Isolation is enforced in layers:

- authentication/authorization
- tenant context derived from verified identity
- EF global query filters
- composite tenant keys and foreign keys
- Tenant A/B integration tests
- PostgreSQL row-level security before public multi-tenant launch

## Consequences

- Unauthenticated tenant-header selection is removed.
- Platform overrides are explicit, authorized and audited.
- Background workers use an explicit system context and tenant predicates.
- Tenant hardening is a launch gate, not post-MVP cleanup.
