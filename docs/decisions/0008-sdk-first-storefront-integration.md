# ADR-0008: One SDK-First Storefront Integration

Status: **Accepted**

Date: **2026-08-20**

## Context

The repository contains a standalone SDK and a separate frontend loader with
different APIs. Neither currently carries a complete secure product/session
contract.

## Decision

`sdk/` becomes the single source of the distributable storefront SDK.

The SDK contract includes:

- store/tenant installation identity
- merchant product and variant identity
- short-lived signed storefront session
- allowed-origin enforcement
- safe iframe or viewer mounting
- origin-checked events
- open, close and destroy lifecycle
- SPA/dynamic product-page support
- semantic versioning and versioned CDN artifacts

The frontend demo consumes the SDK contract rather than maintaining a competing
implementation.

## Rationale

- the product is intended to embed in many commerce platforms
- one contract prevents documentation and runtime drift
- a signed server-issued session protects tenant and product scope
- an isolated iframe reduces merchant-page CSS/JavaScript conflicts

## Consequences

- the current two implementations must be unified
- broad iframe permissions are removed unless a flow explicitly requires them
- `postMessage` requires an explicit schema and origin validation
- platform-specific plugins wrap the same SDK rather than inventing new engines
