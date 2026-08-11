# "While You're Here" 404 — Investigation & Fix

**Reported by:** customer (via Tara), Aug 9 2026 — *"at checkout, the pop-up for
other items brings you to a 404 page… regardless of the product being shown."*
**Status:** root cause found and reproduced. Fix is on the storefront side
(Framer + Shopify publishing), not in this repo.

---

## TL;DR

highspirits.com is a **Framer** site whose store is powered by **Shopify** through
the **Frameship** plugin. Product pages live at **`/shop/<handle>`**.

The **"While You're Here"** upsell in the cart drawer is a Framer component
(`RelatedProductsFromShopify`). Every suggested product is linked with a hard-coded
pattern:

```js
function T(handle){ return `/shop/${handle}` }   // the anchor href, no guard
```

That link 404s for **any suggested product that doesn't have a published
`/shop/` page in Framer** — i.e. products that are *active in Shopify* but *not
published to the sales channel Framer builds pages from*. The component never
checks whether the page exists, so the click lands on the "You've wandered off
the path" 404.

Because the upsell recommends small **companion/accessory** items, and the
accessory catalog is exactly where the publishing gap lives, it looked like it
happened "regardless of the product shown."

## Reproduced (live, today)

| URL | Result |
|---|---|
| `https://highspirits.com/shop/hole-covers` (Leather Hole Cover, active) | **404** |
| `https://highspirits.com/shop/ten-pack-of-leather-tie-kits` (active) | **404** |
| `https://highspirits.com/shop/flute-finger-pads-10-pack` (the $12 item in the screenshot) | 200 |
| `https://highspirits.com/shop/condor-bass-e-spanish-cedar` | 200 |

Method: pulled all 304 **storefront-published** product handles via the Storefront
API and hit every `/shop/<handle>` — **all 304 returned 200**. The only 404s are
products that are active in Shopify Admin but **absent from the storefront**
(not published to the channel). Those are the ones with no Framer page.

> Note: the exact item in the customer's screenshot (Flute Finger Pads, $12) now
> resolves — its page appears to have been (re)published since the Aug 9 report.
> The underlying gap still reproduces on the two accessories above, and will
> recur for any product added to Shopify but not published/synced to Framer.

## Where it comes from (the "backend")

1. **Shopify** — a product is Active but **not published** to the sales channel
   Framer/Frameship reads from (Admin → the product → *Publishing / Sales
   channels*). The Storefront API therefore never returns it.
2. **Framer/Frameship** — because the Storefront API doesn't return it, no
   `/shop/<handle>` CMS page is generated → the URL 404s.
3. **The upsell component** — `RelatedProductsFromShopify` still links to
   `/shop/<handle>` with no "does this page exist?" guard.

## Fix

**A. Data fix (fastest, Shopify + Framer):**
- In Shopify, make sure every product that can appear in the upsell is
  **published to the channel Framer uses** (and the Online Store). Start with the
  confirmed offenders: `hole-covers`, `ten-pack-of-leather-tie-kits`; then audit
  the rest of the **Accessories / add-ons** product type.
- In Framer, **re-sync** the Frameship product data so the missing
  `/shop/<handle>` pages get generated. Verify by hitting the URL directly.
- If a product is *intentionally* not sold on the site (e.g. oversold/hidden),
  it should be **excluded from the upsell's recommendation source** instead of
  published.

**B. Robust fix (prevents recurrence, Framer component):**
- In `RelatedProductsFromShopify`, only render a clickable `/shop/<handle>` link
  for products that actually have a live page, **or** make the upsell card
  *Add-to-Cart-only* (no navigation). A missing page then can never produce a 404.

## Not the cause / ruled out
- Not this repo (`lemoine-explosion-github.js` is a decorative Three.js effect).
- Not the Shopify "Apothecary" theme (that's the legacy myshopify storefront,
  `noindex`, redirects to highspirits.com; it doesn't render the live cart).
- Not a specific broken product — it's a systematic Shopify→Framer publish/sync
  gap plus an unguarded link in the upsell component.
