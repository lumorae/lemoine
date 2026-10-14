# Lemoine: Johnny's flute shorts

Johnny Lemoine films himself playing flutes on his phone and uploads the clips to Google Drive `Inbox/`. You cut them into YouTube Shorts with branded lower thirds and thumbnails, file them on Drive by flute, and maintain the pipeline in `tools/lemoine-cut/`. Every session is a fresh clone of main with no memory of past conversations, so this file is the memory. The code comments (categories.py above all) hold the detail and the history; `tools/lemoine-cut/README.md` describes each tool.

## How to work with Johnny

- He wants a stable, consistent process so he can spend his time creating. The process is your job, not his.
- Never ask him to merge, and don't talk to him about merging. Open and merge your own verified pipeline PRs (see Git). His words: "I don't want to talk about merging things anymore. Can't you just make this process seamless and sturdy?"
- Never make him repeat himself. Before asking anything, check this file and the code comments. If he has answered it before, act on it.
- Make every fix permanent: change the pipeline or template (and its comments), not one output. When he sets a new standing preference, add it here and merge it the same session.
- Don't lose his information. Reusable scripts live in `tools/lemoine-cut/`, merged to main. Deliverables live on Drive. `/home/user/work/dMMDD` is scratch and disappears with the container.
- Defaults without asking: Shorts only, each with a thumbnail. Reels only when he asks.
- Change only what he names. "Thumb only" means replace the thumbnail in place and leave the video.
- Fixes apply from the next cut on. Don't re-cut delivered or scheduled videos unless he asks ("next video only, fine for this one").
- Don't let naming or research hold up a cut. Cut first, research after.
- A flute you can't identify: a wrong guess is worse than an obvious question. Ask him one short question, or file to Unsorted and say so. Never guess a folder.
- When he names the flute, file it as named, even when your eyes say otherwise (see the Red Band trap).
- Report outcomes plainly and briefly. If you were wrong, say so in one line. When he says a video is a dud, believe him and look for the cause.
- Never say something can't be done on platform grounds without checking. If this session can't, say "not from this session" and name the route that works. (He was wrongly told he couldn't upload Shorts thumbnails, and that Studio scheduling was impossible.)

## Session start

1. Read the hook output. A `WARNING` naming an `origin/claude/...` branch with pipeline work not in main means: open a PR for it and merge it yourself now, before anything else (see Git).
2. `NO DRIVE KEY` means cuts stay local. The fix is the `GDRIVE_SA_JSON_B64` environment variable in the environment settings (`base64 -w0 gdrive-sa.json`). Until then say LOCAL ONLY in every report and never claim a filing.
3. On a cut request, before downloading: `df -h /`, `git fetch -q origin && git status -sb`.

## Cutting shorts: the procedure

Run from `/home/user/lemoine`. `T=tools/lemoine-cut`, `W=/home/user/work/dMMDD` (today, Pacific time).

1. **Fetch.** `python3 $T/fetch_inbox.py --out $W/src`, adding `--expect N` when he says N videos (he often asks while his phone is still uploading). Exit 2 = fewer than N arrived, exit 1 = a file never arrived whole, exit 3 = Inbox empty. It names LEFTOVER clips (in Inbox over 12 hours), which count toward N. Safe to re-run.
2. **Identify every flute by sight AND pitch.** `python3 $T/measure.py pitch $W/src/*.MOV`, then look at frames against the Instruments table (maker's mark, wood, bindings). Assign each clip by eye; never assume an even split (six clips once assumed three and three were four and two). When the tuning sits between two note names it prints both readings; pick by eye and the table. The lowest note in Hz is always trustworthy.
3. **Noise.** `-c` only for genuinely noisy locations (a balcony over a city). Two numbers decide it: sub-160 Hz SNR of 1-3 dB is pure rumble (`-c` helps), about 15 dB means the instrument is down there; and a big mid/side gap means the take is already centred, so mono buys nothing. Shakuhachi takes (15-18 dB, 24 dB) were cut without it, Mexico City balcony takes (1-3 dB, 9 dB) needed it. `-n 10/14/18` = gentle/default/aggressive.
4. **Titles.** One distinct title per video (see Titles). Lowercase except the key letter. Use his exact words when he gives a title or a lead.
5. **Fit every title at 42pt** before cutting. Any number under 42 means shorten it:
   `python3 -c "import sys; sys.path.insert(0,'$T'); import make_lower3 as m; g=m.GEOM['vertical-yt']; [print(m.fit_font(f'[ {t} ]', '$T/Outfit-300.ttf', g, 1080)[2], t) for t in sys.argv[1:]]" "title one in D" "title two in G"`
   Drop filler ("the") first. Drop the location only if it still doesn't fit; when he has said where he is, the location is the last thing to go.
6. **Check routing.** `python3 $T/categories.py "x::<title>"` shows where a title files on its own. Put the flute you identified in the jobs.tsv flute column anyway; `-` only when the title alone routes correctly.
7. **Run.** Write `$W/jobs.tsv`, real TAB characters between columns: `id  src/<file>  <flute folder>  <title>  [extra flags: -bw, -c, -p both]`. Start `bash $T/batch_publish.sh $W $W/jobs.tsv` with the Bash tool's `run_in_background` (timeout 7200000). Its exit is the signal: 0 means every job complete. Don't sleep-poll and never use pgrep. If you must check, look at the LAST line only: `tail -n1 $W/runner.txt` (runner.txt is append-only, so an old ALL_DONE from an earlier batch is still in it). `runner.txt` lines: `ok`, `skip`, `FAILED`, `PARTIAL`, `note`.
   After a restart, run the same command again. It skips complete jobs and re-does dead ones. A `PARTIAL` job got its video to Drive but not the rest (usually the thumbnail): finish that by hand, don't re-cut it. Then list the flute folder for a duplicate of any re-cut job (a kill between Drive accepting an upload and the log recording it) and trash the older copy. Tell him plainly what was lost and what re-ran.
8. **Read each log** (`$W/log_<id>.txt`): `flute:` names the right folder and low cut; there is no `lower third: 42pt -> ` (a shrunk cut gets re-cut and the shrunk one trashed); the last line is `PUBLISH_COMPLETE`.
9. **Thumbnails.** `mkdir -p $W/thumbs`. Pick a second by eye from each `*_frames.png` contact sheet: flute in shot, face clear, no angle up the chin. Render under the auto thumbnail's exact name (stamp and slug are on the log's `title:` line):
   `python3 $T/make_short_thumb.py --video $W/src/<file> --at <s> --line1 "<headline>" [--line2 "in D"] --grain 9 --effect diffusion [--fade 0.42] --out $W/thumbs/<STAMP>_<slug>_thumb.jpg`
   `--effect mono` for a `-bw` cut. Check each `-test.png`, then build one row of the whole batch at 180px and change frames until no two read as the same video.
10. **File thumbnails after the run has exited.** One call per flute with only that flute's files: `python3 $T/drive_put.py --flute "<folder>" $W/thumbs/<files>`. `replaced` is normal. `uploaded` is fine only where the run's own thumbnail never got made; then check the name matches the log's stamp and slug. `--trash <prefix>` retires a superseded version: give the OLD version's full `YYYY-MM-DD_HHMM_` stamp, never the stamp you are putting (it would take that cut's video too).
11. **Measure openings.** `python3 $T/measure.py opening $W/*_shorts.mp4`. A gap of 25 dB or more is healthy. 15-25 dB: listen, and look at that flute's low cut (the 10-07 Jayras sat at about 18 dB, which is what led to per-flute low cuts). Under 15 dB is hiss near playing level: stop and fix the pipeline. "opens on the note" means there is no room to measure.
12. **Verify on Drive** before reporting: every cut and thumbnail on Drive matches its local byte count, and `ffmpeg -v error -i <cut> -f null -` prints nothing. After any restart, check Drive itself rather than trusting logs.
13. **Tidy Inbox.** An `IMG_####` source never matches a theme-led cut, so first rename each source on Drive to its cut's title in house form (`Andean Quena Meditation in G.MOV`; Drive API files PATCH `name`, which keeps the link). Then `python3 $T/drive_tidy_inbox.py --dry-run`, then without it; it must end "Inbox is empty".
14. **Previews** with SendUserFile, display render: the tile row first, then one preview per short (`ffmpeg -v error -i <cut> -vf scale=720:1280 -c:v libx264 -crf 30 -preset veryfast -c:a aac -b:a 96k -y $W/p-<slug>.mp4`). Caption: Drive has full quality. For an audio change, add a short before/after clip.
15. **Report.** Per short: title, length, flute folder, Drive link copied from the log, thumbnail headline. Then "sources filed, Inbox empty, everything byte-verified on Drive". When takes look alike, suggest spacing them out when he schedules (see YouTube).
16. **Clean disk.** Delete only local copies already byte-verified on Drive (`$W/src/*.MOV`, old `*_shorts.mp4`). Check `df -h /` again.
17. **Pipeline changed during the job?** Commit, PR and merge after the run has exited (see Git).

**Testing a pipeline change:** always `LEMOINE_LOCAL_ONLY=1` (no key restored, nothing uploaded, even with the Drive variable set), in a copy of the tools with synthetic clips. Unsetting the Drive variables alone once let a test cut reach `Cut/Quena/`.

## Standing creative rules

### Thumbnails
- Brand tokens only, from johnnylemoine.com: `#191919` ink, `#f3efe1` old lace, `#cc3565` coral, all Outfit. Headline lowercase Outfit Bold, eyebrow Outfit Light, lemon mark top-left, photo full frame under the type.
- Headline fixed at 140pt, never shrunk or grown. Long phrases wrap, at most three lines. If one word won't fit the column, change the word.
- Eyebrow fixed at 46pt: `[ a minute of stillness ]`, lowercase, coral dot before it. Never a place name.
- The headline is the hook and says what that video's title leads with: nervous system reset or regulation, creativity, slow breath, a chakra in English or Sanskrit, meditation. Never the wood. Never "just playing" ("not a good hook"). Set `--line1/--line2` whenever the lead isn't the key's chakra; the automatic headline comes from the key ("nervous system reset in G" once got "throat chakra").
- The key line (`in F#`, `in Em`) is optional and always last; drop it if it makes a fourth line or crosses his face ("No need to add the key if that's too long").
- The coral period is drawn by the layout. Never type one (it rendered twice).
- Lines are spaced by baseline with one ink-top offset for the block, so spacing is even. Don't reintroduce per-line offsets.
- The dark top fades into the photo. Default fade 0.58 (he asked for it to come further down into the image). When he is framed high (Mexico City rooms, rooftop) and 0.58 would cross his face, use `--fade 0.42`, the same value for the whole set from that session.
- His face stays clear of type. First find a frame where he sits lower, then drop a line. Never change the size.
- `--grain 9`, `--effect diffusion` on colour.
- Show the flute. A portrait without it only to tell same-session twins apart, and say so when you do.
- Nothing readable in the bottom 18% (the view count sits there). Judge every thumbnail at 180px.
- Colour by default. A red cast is his red light therapy lamp: keep it ("Yes color please. It's red light therapy"). Mono only when he asks for black and white on that video.
- Every short gets a thumbnail unasked. The template applies going forward; the back catalogue before 2026-09-21 has none, on purpose.
- Long-form 16:9 (`make_thumbnail.py`) still auto-fits its sizes. Pin them before using it.

### Titles and lower thirds
- Lead with a theme: nervous system reset or regulation, meditation, or a chakra (English or Sanskrit). "flute meditation" and "quena meditation" are fine and he has asked for them. Never lead with the wood, and never "just playing".
- Every video in a batch gets its own title, lower third and headline. In a mixed batch, cover his themes (nervous system reset, creativity for a D/sacral flute, meditation, chakras) rather than repeating one.
- "Call it ..." or "Lead with ..." means his words exactly. Shorten only what he didn't specify.
- Lower third: one line, 42pt, `[ title ]`, raised Shorts position. Lowercase except the key letter (`in Gm`, never `GM`). No take numbers on screen. No dashes: any dash used as punctuation becomes a comma automatically, but write commas anyway.
- Location: when he says where he is, it goes last as a lowercase clause (`, san diego`, `, mexico city`; he says CDMX, titles say mexico city; a rooftop can be `over mexico city`). Never on the thumbnail.
- `432hz` lowercase, no space, and only for flutes measured at 432: the bamboo Quena and the Spanish Cedar.

### Chakras and Sanskrit
- Key to chakra (a modern Western convention, never call it ancient): C root/Muladhara, D sacral/Svadhisthana, E solar plexus/Manipura, F and F# heart/Anahata, G throat/Vishuddha, A third eye/Ajna, B crown/Sahasrara. Mode doesn't matter (Em is solar plexus). A flute tuned sharp or flat still counts as its key.
- C#, D#, G#, A# have no chakra: fall back to "meditation".
- Use Sanskrit interchangeably with English and bring it in gradually; he is learning it ("I'm down to say sacral and the Sanskrit term for it too, interchangeably"). Alternate across same-chakra videos. He knows solar plexus best. Common glosses: Svadhisthana "one's own place" (creativity, flow), Manipura "city of jewels" (will, confidence), Vishuddha "especially pure" (voice, expression), Anahata "unstruck".
- Only "svadhisthana" routes in categories.py. Any other Sanskrit-led title needs the flute column.

### Voice (titles, descriptions, captions, anything in his name)
- His voice playbook is in his saved preferences: human, specific, short paragraphs, cool and understated, not precious or writerly, never AI, template or LinkedIn-creator. Chakra and meditation copy is warm within that.
- No em dashes ever, no hyphens as dashes, no emojis. Hashtags only at the end of YouTube descriptions or when asked.
- Never fabricate his lived experience; leave a [bracket] for him to fill.
- Bio facts he gave: Johnny in San Diego, runs the design studio Lemoine; playing flute almost two years; plays mid-workday when screen work overwhelms ("the rebellion against society, sometimes it often feels like ... It only helps"); steps into the garden; his cat Sammy comes to listen; the flute is a creative tool for the studio; just started sharing videos, mainly on YouTube.
- Jayras: he described "beautiful walnut ... with ivory tips". Research suggests other wood and bone tips, unverified. Don't name the wood or tip material in copy, and don't claim the name comes from Los Jairas.

### YouTube
- He uploads and schedules in Studio himself. His Studio titles look like `A Minute of Stillness | Sacral Chakra Flow Meditation in D` and can differ from the lower third without a re-cut.
- His descriptions, from the ones he wrote: the flute and key spelled out ("Double drone flute in G minor."); a sentence or two on the note's chakra; "Headphones if you have them."; "Thanks for following my videos!"; "Subscribe for new flute and ambient sessions: https://www.youtube.com/@lemoinemusic"; "Website: https://johnnylemoine.com"; "Instagram: https://www.instagram.com/lemoinedesign"; hashtags such as #chakrahealing #nativeflute #meditationmusic #flutemusic #soundhealing #nervoussystemreset.
- He mostly posts one Short a day, scheduled a few days ahead, around 9-10 AM Mexico City time. When he asks for scheduling help, put an upload sheet in a folder on Drive (not loose at the top of Cut/): slot, video and thumbnail links copied from logs, title, description, hashtags. Studio needs a session on his computer with screen control (Claude Desktop, `claude remote-control`, Claude in Chrome), not this cloud session. Never upload with the YouTube Data API: unverified projects lock videos to private.
- Shorts run up to 3 minutes. The Shorts feed autoplays without a thumbnail; thumbnails show in the channel grid, search and suggested. Views settle over 2-3 days. Public counts: `https://www.youtube.com/feeds/videos.xml?channel_id=UCvyGfbB-0A_NTwhnad9EEEQ`. Impressions, CTR and "Viewed vs. swiped away" are Studio-only.
- Duds: look at the data first (RSS plus the back catalogue). The working hypothesis for the October duds is sameness: same-session lookalikes (room, outfit, flute, theme) on consecutive days. It isn't proven, so offer it as a suggestion when he schedules, not a rule.
- `yt_stats.py` (Studio analytics) is waiting on his side: consent screen, test user and Desktop OAuth client on project analytics-501817, then `--init`, `--auth-url`, `--auth-code`. Steps in `tools/lemoine-cut/SETUP-yt-stats.md`.

### Sound (lemoine_cut.sh is the source of truth)
- Reverb: convolution with `ir-hall.wav` via reverb.py, wet -9 dB (was -12; he heard it as weak). If he still finds it weak, -6 is the next step to offer.
- Loudness: one fixed gain to -14 LUFS, then a limiter that only turns peaks down. Never loudnorm as a processor, single pass or linear: it is an automatic gain control and lifted the room before the first note by about 33 dB on every short before 2026-10-04.
- No automatic or timed fade keyed to the first note ("sometimes I start playing earlier and sometimes later"). Only the fixed short fade in and out. No trim to the first note.
- Low cut per flute from categories.py, only where measured, never global (a global one would thin the drone flutes), applied before the reverb.
- Audio is stream a:0 (the iPhone spatial track can't be decoded).
- Black and white only when he asks for that video: `-bw`. Footage goes mono, overlays stay coral and cream, the thumbnail goes mono.
- Reels only when asked: `-p reels` or `-p both`.

## Instruments

Folder = `LEMOINE_FLUTE` = the jobs.tsv flute column. Exactly these; an unknown name stops the run. Tunings are measured unless marked.

| Folder | Key, chakra | Recognise by | Measured | Low cut | A title alone routes here when it has |
|---|---|---|---|---|---|
| High Spirits Double F# | F#, heart | crossbow-shaped double, drone + melody chambers joined by a cross-bar | drone 366-370 Hz, F#4 (three takes) | 180 | F#, and not "spirit flute" |
| Spirit Flute F# | F#, heart | single chamber, reddish, carved spiral/flame marks | F# minor pentatonic near A440; lowest 366-369 Hz (three takes) | 180 | F# and "spirit flute" |
| High Spirits Nova G | G (Gm), throat | pale, striped double | not measured | none | G, and no quena word |
| Ebonized Walnut A | A, third eye | the only A flute | not measured | none | A |
| High Kestrel D | D, sacral | High Spirits; carved bird | not measured | none | D and "kestrel" |
| Stellar Flute D | D, sacral | Stellar Flutes; plain reddish body, no burned symbols, black block tie, red/white/grey woven band; also the shaker clips | D dorian, about A445-447; lowest about 291-296 Hz | 140 | D and "stellar" or "shaker" |
| Sacral Chakra D | D, sacral | High Spirits; reddish single chamber, burned svadhisthana medallion near the foot | D dorian, about A447; lowest about 296 Hz | 140 | D and "sacral", "chakra" or "svadhisthana" |
| Spanish Cedar 432Hz | E minor, solar plexus | honey wood, block and leather binding, concentric-arc maker's mark | A430.6-433; lowest about 312-322 Hz | 150 | "spanish cedar", "432" or "432hz", any key |
| Shakuhachi | none | | not measured | none | "shakuhachi" |
| Quena Jayras | G, throat | dark wood, burned QUENAS JAYRAS stamp, pale chakana inlay near the top, black cloth wrap with a tab over two blue-and-white woven bands and a brown beaded band, pale U-notch mouthpiece | about A426-434; notes 387, 428, 477, 504, 622 Hz; lowest G4 about 383-391 Hz | 200 | "jayras" (so always set the flute column) |
| Quena | G, throat | bamboo/cane Andean notched flute | G major pentatonic at about A431 (several takes, two continents); lowest G4 about 383 Hz | 200 | "quena", with G or no key |
| Black Quena | F#, heart | the second Mexico City market quena: black wood, plain, no mark | notes 370, 412, 466, 500, 562, 619, 679 Hz; home note F#4 370 Hz | 180 | "quena" with F# |

- Keys are shared (three F#, three D, and the Nova plus three quenas in or near G/F#). Never file by key alone; identify by sight and pitch, and put the flute in the column.
- The two Mexico City quenas clash if played together: about 75 cents apart at the bottom, nearly together at the top.
- Under warm indoor light the Jayras's bands look different (the brown beaded band reads red-and-black, blue-and-white goes grey). Confirm by the chakana, the stamp and the pitch, never band colour.
- Aliases he uses: "drone/double drone/double flute in F#" is the Double; "drone flute Gm", "double nova", "double drone nova" are the Nova. MAP keeps `drone-in-mexico-city` (Nova) and `nervous-system-reset-new-quena-in-g` (Jayras).
- Copy claims only measured tuning: 432 is the bamboo Quena and the Spanish Cedar; the Jayras is about 430; the D flutes (about 447) and the Double (440) are not 432.
- Record a tuning as fact after a second independent take. A folder may be renamed when he names a flute (`Shaker and Flute D` became `Stellar Flute D`): move the cuts by changing their parent and keep a MAP entry for old slugs. Don't rename for no gain.
- A new flute: add a FLUTES entry in categories.py (folder, key or keyless words, what it looks like, what it measures, low cut an octave under its lowest note) before its first cut, so the cut files and filters correctly from the start.

## Drive

- `Inbox/` holds only clips still to cut. `Source/<Flute>/` holds cut originals. `Cut/<Flute>/` holds cuts and their `_thumb.jpg`. `Cut/INDEX.md` lists every cut with its title and thumbnail link; it is rewritten in place (its link never changes) by every publish and every `drive_put.py`.
- Filenames are `YYYY-MM-DD_HHMM_<slug>[-takeNN]_shorts.mp4`, dated in Pacific time (built in; don't override TZ).
- Keep every link working: move by changing the parent, update by replacing content in place (`drive_put.py`), retire with trash (recoverable for 30 days). Never permanently delete, never use a loose `name contains` query.
- A misfiled cut: move it, its `_thumb.jpg` and its source by changing their parents (`addParents`/`removeParents`), then rebuild the index. `drive_migrate.py` can't do this: it only sees slugs, so it never touches a folder a flute owns, and it only rescues cuts from date folders, Unsorted and retired folders (dry run unless `--apply`).
- Copy every Drive URL from an `uploaded:` or `replaced` line or a fresh listing. Never type or recall an ID (two were once invented in a summary).
- The service-account scripts handle anything video-sized. The claude.ai Drive connector downloads at most 10 MB and can't upload video.
- `drive_upload.py` without `--subfolder` puts a file loose at the top of `Cut/`. About 35 loose files sit there from before (IG reels and covers, `THUMB-*.jpg`, upload sheets, `fixed.mp4` from a 10-04 test); some are his deliverables, so leave them unless he asks.

## Git and merging

1. Branch only from a fetched main, and only when your current branch has nothing unmerged: `git fetch -q origin`, check `git rev-list --count origin/main..HEAD` is 0, then `git checkout -q -B <your claude/ branch> origin/main`. `checkout -B` resets the branch and drops any unmerged commits on it; merge those first. (After PR #7 a branch was cut from a stale origin/main.)
2. Commit and push early. The container restarts without warning and takes uncommitted work with it.
3. Never switch branches or edit pipeline files while a publish run is going: it would swap scripts under the running job.
4. Test pipeline changes with `LEMOINE_LOCAL_ONLY=1` in a copy of the tools (see the procedure).
5. Pipeline changes (`tools/lemoine-cut`, `.claude`, this file) go through a PR that you open AND merge yourself once verified, in the same session, without asking. Load `mcp__github__create_pull_request` and `mcp__github__merge_pull_request` with ToolSearch; the repo is `lumorae/lemoine`.
6. Before merging: `git fetch`; local HEAD equals `origin/<branch>` and what you tested; `git rev-list --count HEAD..origin/main` is 0 (otherwise merge main in and re-test). Merge with `expectedHeadSha` set to that HEAD.
7. After merging: fetch, confirm with `git show origin/main:<file> | grep <change>`, and run `CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=/home/user/lemoine bash .claude/hooks/session-start.sh` until it is clean.
8. The hook's WARNING only watches branches that touch `tools/lemoine-cut` or `.claude`, so a change to this file alone is not flagged; merge it anyway. Leave other sessions' branches alone (etsy, flodesk, soma, social strategy and so on). `origin/claude/pure-bliss-airtable-fwvd2g` has its own CLAUDE.md (his writing-voice playbook); if it is ever merged, combine the two files.

## Known traps

- **The Red Band misfile (2026-10-10).** A lamp changed the Jayras's band colours, a take was filed into an invented "Quena Red Band" folder, and he had to ask where it went. File as he names it.
- **Theme-led titles route by key alone.** Jayras titles go to the Nova (G) or the bamboo Quena ("quena"); F# titles go to the Double; D titles go to Unsorted, and any "chakra" pulls a Stellar or Kestrel take into Sacral Chakra D; any "432" goes to the Spanish Cedar whatever the key. The flute column fixes all of these.
- **A hand-capitalised title** ("Stellar Flute in D") reads the F of "Flute" as the key and files to the Double. Lowercase except the key.
- **make_lower3.py shrinks long titles silently** (to as low as 30pt, warning only on stderr). Fit-test at 42pt first.
- **Hand thumbnails vs the run's own upload.** The run uploads its automatic thumbnail at the end; a hand render put before the run finishes gets overtaken. `drive_put.py` only after the run has exited.
- **Every thumbnail goes to Drive.** Thumbnails left in the workdir were lost with the container.
- **A run reported as "no output"** was writing to its log. Read `log_<id>.txt`.
- **Container restarts** killed work on 09-23 and twice on 10-08. The runner, fetch and Drive tools are built to be re-run; verify on Drive before reporting what survived.
- **ffmpeg reads stdin** while it encodes. Under the old runner it ate the job list. Every ffmpeg now has `-nostdin` and jobs run with stdin from /dev/null; keep it that way in any new script.
- **pgrep matched its own shell**, and once read "(01)" as a regex group. Never wait on process names.
- **Two publishes at once** deleted each other's frames. One runner per workdir (it is locked).
- **Downloads arrive short** through the proxy (three of six on 09-27). Only `fetch_inbox.py`.
- **A pitch reading can be a semitone off** when a flute sits far from 440 (the Jayras is about 57 cents flat). `measure.py` prints both readings; decide by eye.
- **A double flute's two voices make a phantom low note.** Drone plus a melody note a fifth above repeat together an octave under the drone, which is where the old "184 Hz drone" came from. `measure.py` now drops any "note" with no energy at its own fundamental.
- **A "dash" in a title** shows on screen. The publish script now turns dashes into commas.
- **Unmerged work vanishes.** On 10-04 a fresh container came up without three weeks of fixes (it would have cut reels with no thumbnail); the session noticed. Merge yourself, the same session.
- **Isolated tests reached Drive** twice (`fixed.mp4` on 10-04, a lock test on 10-11). `LEMOINE_LOCAL_ONLY=1`.

## Open threads

- Offered and not taken up, so don't re-offer unprompted: swapping the stale Sept 12-14 walnut thumbnails; a no-fade loop-preserving variant of the sacral audio; "flute meditation" as the permanent thumbnail default.
- Lost with old containers, never committed: `build_reel.sh` (IG reels from the long-form, segment 2 offset +31.68 s), `pick_2min.py` (2-minute window picker, crop safety gated on the mean, at most 0.24), `assess.py`, and the MIDI helpers `mkmidi.py`/`melody.py` (melody clarity at least 0.82, range C4-E5, pentatonic snap). Rebuild from these notes if he asks for long-form or IG work again, and commit them this time.
