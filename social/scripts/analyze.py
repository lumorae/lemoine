#!/usr/bin/env python3
"""Quick content audit for Lemoine Instagram.

Usage:
    python3 analyze.py ../data/ig_snapshot_2026-06-23.json

Reads a media JSON (the shape returned by graph.instagram.com /me/media) and
prints the patterns we care about: engagement by theme, format, caption length,
hashtag count, and day of week, plus top/bottom posts.

To pull a fresh snapshot (token NOT stored in repo — paste at runtime):
    TOK=<token>; curl -s \
      "https://graph.instagram.com/v21.0/me/media?fields=id,caption,media_type,timestamp,like_count,comments_count,permalink&limit=50&access_token=$TOK" \
      -o ../data/ig_snapshot_$(date +%F).json
"""
import json, re, sys
from collections import Counter, defaultdict
from datetime import datetime

PERSONAL = ["sober","drink","sobriety","mental","anxiet","fear","afraid","struggl",
            "honest","vulnerab","myself","scared","cried","therapy","fall","fell",
            "heart","journey","grief","alone","depress"]
BUSINESS = ["brand","client","strategy","logo","design","website","process","tips",
            "how to","steps","framework","business","entrepreneur","marketing"]

def eng(p): return p.get("like_count",0) + p.get("comments_count",0)

def theme(p):
    c = (p.get("caption","") or "").lower()
    ps, bs = sum(c.count(k) for k in PERSONAL), sum(c.count(k) for k in BUSINESS)
    return "personal" if ps > bs else ("business" if bs > ps else "mixed")

def avg(xs): return round(sum(xs)/len(xs), 1) if xs else 0

def group(posts, keyfn):
    g = defaultdict(list)
    for p in posts: g[keyfn(p)].append(eng(p))
    return {k: (len(v), avg(v)) for k, v in g.items()}

def main(path):
    posts = json.load(open(path))["data"]
    print(f"{len(posts)} posts | avg eng {avg([eng(p) for p in posts])}\n")
    print("THEME       ", group(posts, theme))
    print("FORMAT      ", group(posts, lambda p: p["media_type"]))
    print("HASHTAGS    ", group(posts, lambda p: str(len(re.findall(r'#\w+', p.get('caption','') or '')))))
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    print("DAY         ", group(posts, lambda p: days[datetime.fromisoformat(p['timestamp'].replace('+0000','+00:00')).weekday()]))
    print("\nTOP 5:")
    for p in sorted(posts, key=eng, reverse=True)[:5]:
        print(f"  {eng(p):3}  {p['timestamp'][:10]}  {(p.get('caption','') or '')[:60].strip()}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../data/ig_snapshot_2026-06-23.json")
