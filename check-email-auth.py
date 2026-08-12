#!/usr/bin/env python3
"""Check SPF, DKIM and DMARC for the Lemoine mail domains.

Run this before and after making DNS changes to confirm they actually landed.
Resolves over DNS-over-HTTPS so it needs no `dig` and no third-party packages.

    ./check-email-auth.py                        # both domains
    ./check-email-auth.py johnnylemoine.com      # one domain
    ./check-email-auth.py --selectors k1,fd1     # probe extra DKIM selectors

Exit code is 0 when every domain passes, 1 when anything fails.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

DOH = "https://dns.google/resolve"
DEFAULT_DOMAINS = ["johnnylemoine.com", "lemoinedesign.com"]

# DKIM selectors cannot be enumerated from DNS -- a key is only discoverable if
# you already know its selector. This is the set worth probing for the senders
# in play here; add more with --selectors.
SELECTORS = [
    "google",           # Google Workspace default
    "zoho", "zmail",    # Zoho
    "fd1", "fd2",       # Flodesk
    "default", "dkim", "mail", "smtp", "email",
    "selector1", "selector2",  # Microsoft 365
    "s1", "s2", "k1", "k2", "k3",
    "mandrill", "sendgrid", "sm", "pm", "mailjet",
]

PASS, WARN, FAIL, INFO = "PASS", "WARN", "FAIL", "INFO"
MARK = {PASS: "[ ok ]", WARN: "[warn]", FAIL: "[FAIL]", INFO: "[ -- ]"}


def resolve(name, rrtype):
    """Return a list of record strings, or [] for NXDOMAIN / empty."""
    url = f"{DOH}?{urllib.parse.urlencode({'name': name, 'type': rrtype})}"
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as exc:
        raise RuntimeError(f"DNS query failed for {name} {rrtype}: {exc}") from exc
    return [normalise_txt(a["data"]) for a in data.get("Answer", []) if "data" in a]


def normalise_txt(value):
    """Join the quoted 255-byte chunks a long TXT record is split into."""
    if '"' not in value:
        return value.strip()
    return "".join(part for part in value.split('"')[1::2])


def spf_records(domain):
    return [r for r in resolve(domain, "TXT") if r.lower().startswith("v=spf1")]


def count_spf_lookups(domain, seen=None, depth=0):
    """Count the DNS-querying mechanisms in an SPF record.

    RFC 7208 caps this at 10; exceeding it makes SPF permerror, which most
    receivers treat as a failure.
    """
    if seen is None:
        seen = set()
    if domain in seen or depth > 10:
        return 0
    seen.add(domain)

    records = spf_records(domain)
    if not records:
        return 0

    total = 0
    for term in records[0].split():
        mechanism, _, target = term.partition(":")
        mechanism = mechanism.lstrip("+-~?").lower()
        if mechanism in ("a", "mx", "ptr", "exists"):
            total += 1
        elif mechanism == "include" and target:
            total += 1 + count_spf_lookups(target, seen, depth + 1)
        elif mechanism == "redirect" or term.lower().startswith("redirect="):
            _, _, redirect_target = term.partition("=")
            if redirect_target:
                total += count_spf_lookups(redirect_target, seen, depth + 1)
    return total


def check_mx(domain, out):
    records = resolve(domain, "MX")
    if not records:
        out(FAIL, "MX", "no MX records -- this domain cannot receive mail")
        return None

    hosts = " ".join(records).lower()
    provider = next(
        (name for token, name in (
            ("aspmx.l.google.com", "Google Workspace"),
            ("zoho", "Zoho Mail"),
            ("outlook.com", "Microsoft 365"),
            ("messagingengine", "Fastmail"),
        ) if token in hosts),
        "unknown provider",
    )
    out(INFO, "MX", f"{provider} ({len(records)} records)")
    return provider


def check_spf(domain, out):
    records = spf_records(domain)
    if not records:
        out(FAIL, "SPF", "no SPF record -- unauthenticated senders are unchallenged")
        return False
    if len(records) > 1:
        out(FAIL, "SPF", f"{len(records)} SPF records; RFC 7208 permits exactly one")
        return False

    record = records[0]
    out(INFO, "SPF", record)

    ok = True
    lookups = count_spf_lookups(domain)
    if lookups > 10:
        out(FAIL, "SPF", f"{lookups} DNS lookups, over the limit of 10 (permerror)")
        ok = False
    elif lookups > 7:
        out(WARN, "SPF", f"{lookups} DNS lookups, close to the limit of 10")
    else:
        out(PASS, "SPF", f"{lookups} DNS lookups, within the limit of 10")

    if "_spfm." in record:
        out(WARN, "SPF", "routed via GoDaddy SPF-merge; inlining the real "
                         "includes removes a lookup and a dependency")
    if record.rstrip().endswith("+all"):
        out(FAIL, "SPF", "ends in +all, which authorises the entire internet")
        ok = False
    return ok


def parse_tags(record):
    tags = {}
    for part in record.split(";"):
        key, _, value = part.strip().partition("=")
        if key:
            tags[key.strip().lower()] = value.strip()
    return tags


def rsa_key_bits(public_key):
    """Approximate the modulus size of a base64 DER-encoded RSA public key."""
    try:
        import base64
        der = base64.b64decode(public_key + "=" * (-len(public_key) % 4))
    except Exception:
        return None
    # Close enough to distinguish 1024 from 2048 without a crypto dependency.
    return 1024 if len(der) < 200 else 2048


def check_dkim(domain, selectors, out):
    found = []
    for selector in selectors:
        for record in resolve(f"{selector}._domainkey.{domain}", "TXT"):
            tags = parse_tags(record)
            if "p" in tags:
                found.append((selector, tags["p"]))

    if not found:
        out(FAIL, "DKIM", f"no key on any of {len(selectors)} probed selectors")
        out(INFO, "DKIM", "without a domain-aligned key, Google signs as "
                          "*.gappssmtp.com and receivers see the domain as unsigned")
        return False

    ok = True
    for selector, public_key in found:
        if not public_key:
            out(FAIL, "DKIM", f"{selector}._domainkey has an empty p= (revoked key)")
            ok = False
            continue
        bits = rsa_key_bits(public_key)
        if bits == 1024:
            out(WARN, "DKIM", f"key at {selector}._domainkey looks like 1024-bit; "
                              "2048-bit is the current norm")
        else:
            out(PASS, "DKIM", f"key published at {selector}._domainkey")
    return ok


def check_dmarc(domain, out):
    records = [r for r in resolve(f"_dmarc.{domain}", "TXT")
               if r.lower().startswith("v=dmarc1")]
    if not records:
        out(FAIL, "DMARC", "no DMARC record -- nothing tells receivers what to "
                           "do with mail that fails authentication")
        return False

    record = records[0]
    out(INFO, "DMARC", record)

    tags = parse_tags(record)

    ok = True
    policy = tags.get("p", "").lower()
    if policy in ("quarantine", "reject"):
        out(PASS, "DMARC", f"policy p={policy} is enforcing")
    elif policy == "none":
        out(WARN, "DMARC", "policy p=none monitors but enforces nothing; move to "
                           "quarantine once reports look clean")
    else:
        out(FAIL, "DMARC", f"missing or invalid policy tag (p={policy!r})")
        ok = False

    if tags.get("rua"):
        out(PASS, "DMARC", f"aggregate reports to {tags['rua']}")
    else:
        out(WARN, "DMARC", "no rua= address, so no visibility into what fails")
    return ok


def check_domain(domain, selectors):
    print(f"\n{domain}")
    print("-" * len(domain))

    results = []

    def out(status, label, message):
        results.append(status)
        print(f"  {MARK[status]} {label:<6} {message}")

    check_mx(domain, out)
    check_spf(domain, out)
    check_dkim(domain, selectors, out)
    check_dmarc(domain, out)
    return FAIL not in results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("domains", nargs="*", default=DEFAULT_DOMAINS,
                        help="domains to check (default: %(default)s)")
    parser.add_argument("--selectors", default="",
                        help="comma-separated extra DKIM selectors to probe")
    args = parser.parse_args()

    selectors = list(SELECTORS)
    selectors += [s.strip() for s in args.selectors.split(",") if s.strip()]

    try:
        ok = all([check_domain(d, selectors) for d in args.domains])
    except RuntimeError as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 2

    print("\nall checks passed" if ok else "\nfailures above need fixing")
    print("note: DKIM selectors cannot be enumerated from DNS. A key on a "
          "selector outside the probe list\n      will read as missing -- pass "
          "it with --selectors.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
