# HANDOFF — publish the High Spirits launch carousel to Instagram

You are a fresh Claude Code session running **locally on the user's Mac**. A prior
(cloud) session set everything up but could not reach the user's local files. Your
job: publish one **mixed photo + video carousel** to Instagram, hands-free. The user
(Johnny, @lemoinedesign) does NOT want to touch the Instagram app.

## What's already true
- Instagram is connected via the **Instagram Login** flow (`graph.instagram.com`).
- Reading + insights are verified working. **Publishing has NOT been tested yet —
  this is the first real post.** The `instagram_business_content_publish` permission
  is added, so it should work; if it errors, report the exact API message.
- Account: **@lemoinedesign**, IG user id **17841401720504053**, type BUSINESS.
- This repo (`lumorae/lemoine`) is **public**, branch
  `claude/lemoine-social-strategy-389btq`. That matters: we host the media here and
  hand Instagram the `raw.githubusercontent.com` URLs (IG can only pull public URLs).
- A ready publisher lives at `social/scripts/post_carousel.py` (stdlib only). It
  creates child containers (photo + video), waits for video processing, builds the
  CAROUSEL parent, publishes, and prints the live permalink. It reads the token from
  `tok.txt` in the current working directory.

## The media (in the user's folder)
`~/Desktop/Design/High Spirits Flutes/Social/IG/` — six files labeled 1–6.
**Order is exact — do not reorder:**

| # | Type | Content |
|---|------|---------|
| 1 | photo | two flutes on a desert rock |
| 2 | video | `High_Spirits_IG_2.mp4` |
| 3 | photo | flute + laptop, "Shop the Flute Collection" |
| 4 | video | `High_Spirits_IG_4.mp4` |
| 5 | photo | HSF homepage on a workbench |
| 6 | photo | Lemoine sign-off |

Map files by the number in each filename (…_1/_3/_5/_6 = photos, …_2/_4 = videos).

## Steps
1. `cd` to a work dir (e.g. this repo root after cloning). Confirm `python3 --version`.
2. Copy the 6 files into `social/posts/high-spirits-launch/` renamed
   `01.png 02.mp4 03.png 04.mp4 05.png 06.png` (pad to 2 digits so they sort right).
3. `git add` those media, commit, and **push** to `claude/lemoine-social-strategy-389btq`.
   (They must be pushed before IG can fetch them.)
4. Create `tok.txt` in your work dir containing the access token (ask the user to
   paste it — it's a secret, do NOT commit it; it's already in `.gitignore`).
5. Build `manifest.json` (do NOT commit it) with the 6 raw URLs **in order**:
   `https://raw.githubusercontent.com/lumorae/lemoine/claude/lemoine-social-strategy-389btq/social/posts/high-spirits-launch/01.png` … etc.
   ```json
   {
     "caption": "<see caption below>",
     "items": [
       {"url": ".../01.png", "type": "image"},
       {"url": ".../02.mp4", "type": "video"},
       {"url": ".../03.png", "type": "image"},
       {"url": ".../04.mp4", "type": "video"},
       {"url": ".../05.png", "type": "image"},
       {"url": ".../06.png", "type": "image"}
     ]
   }
   ```
6. Run: `python3 <repo>/social/scripts/post_carousel.py manifest.json`
   It prints `LIVE AT: <permalink>` on success. Give that link to the user.
7. Optional cleanup: after it's live, remove the media from the repo and push (IG
   keeps its own copy once published).

## Known risks + fallbacks
- **Video via GitHub raw:** if IG's video containers return an error or never reach
  `FINISHED`, the likely cause is content-type/host. Fallback: host the two MP4s on a
  real CDN — the user has **Vercel** (team "Lemoine's projects"); `vercel deploy` a
  folder of the media and use those URLs instead. Or any public https host.
- **Aspect ratio:** carousel children should share a ratio (the stills look 4:5,
  1080×1350). If a video is a different ratio IG may crop or reject; if rejected,
  tell the user so they can re-export the video at 1080×1350.
- **Silent video:** if IG rejects a video with no audio track, add a silent track.

## Caption (final, in the user's voice — do not edit)
```
One year ago, on my birthday, I bought a flute I couldn't really afford.

It was in a little sound healing shop on a road trip through Arizona. I played it once and something in me just understood. That flute has been with me almost every day since, along with fourteen others. Our house slowly turned into a little sound healing temple, and it has brought me more peace than almost anything I have ever tried.

It was made by a company called High Spirits Flutes. So I finally reached out. I wasn't pitching them. I just wanted to say thank you from the core of my heart.

And then I got to build their brand.

It went live last week and I gave it everything I had. Swipe through, and if it moves you, go meet them at highspirits.com

Love,
Johnny
```
