---
name: mobile-web-camera-upload
description: Build mobile-web photo upload flows (camera + gallery, multi-file, client-side compression) that work reliably across Android/iOS browsers. Covers the `capture` attribute trap, multi-file form handling, auto-reopen camera failures, and the one-tap-per-photo fallback. Use whenever a web app needs phone-camera photo input for inventory, listings, field data, or forms.
---

# Mobile Web Camera Upload

Class of work: any web app where a phone user adds photos via camera or gallery (inventory, listings, field reports, receipts, ID capture). The mobile browser behaviors here are **durable platform facts**, not session-specific quirks.

## The `capture` attribute trap (most important)

```html
<!-- FORCES camera-only on most mobile browsers — blocks gallery -->
<input type="file" accept="image/*" capture="environment" />

<!-- ALLOWS both camera AND gallery — phone shows the standard chooser -->
<input type="file" accept="image/*" />
```

`capture="environment"` tells the browser "open the rear camera immediately and skip the gallery picker." This is a **one-way door** on Android Chrome and Samsung Internet: the user cannot reach their gallery from that input. Verified 2026-07-30 on the booth app — girlfriend could only take live photos, never pick existing/Canva-cleaned images.

### When to use each

| Goal | Markup |
|---|---|
| User is shooting items live at a booth/site (fast snap loop) | `capture="environment"` — but see auto-reopen caveat below |
| User may pick from gallery OR shoot live | **omit `capture`** — standard chooser (Camera / Gallery / Files / Drive) |
| Both paths needed | Two separate buttons: one input with `capture`, one without. Don't try to make one input do both. |

**Default recommendation:** omit `capture`. The standard chooser is what Facebook Marketplace, eBay, Poshmark, and every mature listing app use. Only add `capture` when the user explicitly wants a fast live-snap loop AND you've tested the auto-reopen behavior on their actual phone.

## Multi-file upload: `form.get` vs `form.getAll`

```ts
// BUG — only returns the FIRST file even if input has multiple
const photo = form.get('photo')
if (photo instanceof File && photo.size > 0) { ... }

// CORRECT — returns ALL files from <input name="photos" multiple>
const photos = form.getAll('photos').filter(
  (f): f is File => f instanceof File && f.size > 0
)
```

`FormData.get(name)` returns the **first** value for a repeated field. For `<input multiple>` you MUST use `getAll(name)`. This bug silently saves only the first photo and is invisible in manual testing if you only ever pick one photo. Verified 2026-07-30 — booth app saved 1 of 3 uploaded photos until this was fixed.

Also: the input's `name` must match what `getAll` reads. If the input is `name="photos"` and the route reads `getAll('photo')`, you get an empty array with no error.

## Auto-reopen camera is unreliable on Android OEMs

The "rapid capture" pattern — open camera, on `change` save the shot, then `setTimeout(() => input.click(), 50)` to reopen — works on **most** Android browsers but **fails on some OEM camera apps** that don't return focus to the page cleanly after a shot. Symptom: first photo saves, then the camera never reopens; the UI gets stuck on "Compressing…".

```js
// UNRELIABLE — fails on some Samsung/Xiaomi/Pixel OEM camera apps
input.addEventListener('change', async () => {
  await handleShot(input.files[0])
  input.value = ''
  setTimeout(() => input.click(), 50)  // may never fire
})
```

### Reliable fallback: one tap per photo

```js
// RELIABLE — each tap is a fresh user-initiated camera open
let taken = 0
const MAX = 5
btn.addEventListener('click', () => {
  if (taken >= MAX) return
  input.click()  // user tapped → camera opens → snap → closes
})
input.addEventListener('change', async () => {
  const f = input.files?.[0]
  if (!f) return
  input.value = ''  // reset so same file can be re-picked
  await handleShot(f)
  taken++
  btn.textContent = `📸 Take photo ${taken + 1} of ${MAX} (${taken} done)`
  if (taken >= MAX) { btn.disabled = true; btn.textContent = `✓ ${MAX} photos taken (max)` }
})
```

One tap = one photo. The button relabels itself so the user always knows where they are. No auto-reopen, no Stop button, no stuck state. This is the pattern to ship by default; only attempt auto-reopen if the user explicitly wants it AND you've tested on their phone.

## Client-side compression (do it, always)

Phone cameras produce 4–12 MP JPEGs (3–8 MB). Uploading raw wastes bandwidth, disk, and R2 quota. Compress in the browser before upload:

```js
async function compress(file, maxDim = 1200, quality = 0.8) {
  const img = await loadImg(file)              // new Image + URL.createObjectURL
  let { width, height } = img
  if (width > height && width > maxDim) { height = Math.round(height * maxDim / width); width = maxDim }
  else if (height > maxDim) { width = Math.round(width * maxDim / height); height = maxDim }
  const canvas = document.createElement('canvas')
  canvas.width = width; canvas.height = height
  canvas.getContext('2d').drawImage(img, 0, 0, width, height)
  const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', quality))
  return new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' })
}
```

- max **1200px** longest side is plenty for web gallery thumbnails and detail pages
- JPEG **q0.8** keeps files ~100–400 KB (from 3–8 MB originals)
- Always **fall back to the original file** if compression throws (broken EXIF, rare format)
- Replace the input's FileList via `DataTransfer` so the form submits the compressed blob, not the original

```js
const dt = new DataTransfer()
dt.items.add(compressedFile)
input.files = dt.files
```

## Pending-photo UI (don't lose the user's shots)

Show a live thumbnail grid of queued photos with a ✕ on each to remove. Keep the queue in a JS array (`compressedFiles`), not just in the input's FileList — the FileList is fragile and re-syncing it on every remove is error-prone.

```js
function syncInput() {
  const dt = new DataTransfer()
  compressedFiles.forEach(f => dt.items.add(f))
  input.files = dt.files
  pending.innerHTML = compressedFiles.map((f, i) =>
    '<div class="ph-card"><img src="' + URL.createObjectURL(f) + '" /><button data-i="' + i + '">✕</button></div>'
  ).join('')
}
```

## Double-submit guard + the disabled-button-drops-intent trap

Phone users double-tap save buttons. Guard against it — but the obvious guard introduces a **silent, nasty bug**.

### The bug

```js
// GUARD — disables buttons on submit
form.addEventListener('submit', (e) => {
  form.querySelectorAll('button[type="submit"]').forEach(b => b.disabled = true)
})
```

```html
<!-- Two submit buttons distinguished by name/value -->
<button type="submit" name="intent" value="next">Save &amp; add next</button>
<button type="submit" name="intent" value="done">Save &amp; done</button>
```

**A disabled submit button does NOT include its `name`/`value` in the submitted form data.** So once the guard disables the buttons, `form.get('intent')` returns `null`, the route defaults to `'done'`, and "Save & add next" silently becomes "Save & done" → user lands on the dashboard instead of a fresh add form. Verified 2026-07-30 — booth "Save & add next" broke the moment double-submit protection was added; user saw "Save and next goes to dashboard" and had to escalate.

### Workflow rule: never silently remove "Save & add next"

The two-button save pattern is **the whole point** of a batch-photographing workflow (girlfriend snapping 30 booth items in a row). When "simplifying" the UI, do NOT collapse the two buttons into one "Save → dashboard" button — that destroys the loop and forces a tap back to Add between every item. Verified 2026-07-30: I removed "Save & add next" during a "simplify the buttons" pass, the user immediately asked "What happened to save & next button?", and restoring it was the next task. The batch loop is a load-bearing feature, not UI clutter.

This bug is invisible in single-button forms (only one intent) and only surfaces when a second button's value matters — exactly the camera-upload batch loop where "Save & add next" is the whole point.

### The fix: hidden intent field + `data-intent`

```html
<input type="hidden" name="intent" id="intent-field" value="done" />
<button type="submit" data-intent="next">Save &amp; add next</button>
<button type="submit" data-intent="done">Save &amp; done</button>
```

```js
// Set the hidden field from data-intent BEFORE the disable fires
document.querySelectorAll('button[data-intent]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('intent-field').value = btn.dataset.intent
  })
})
// Now the disable-on-submit guard is safe — the intent is already in a hidden input
form.addEventListener('submit', (e) => {
  form.querySelectorAll('button[type="submit"]').forEach(b => b.disabled = true)
})
```

The hidden field is always submitted (it's never disabled), so the server reliably reads `form.get('intent')`. The buttons carry only `data-intent`, never `name`/`value` that could be dropped.

### Rule

**Never rely on a submit button's own `name`/`value` reaching the server if any double-submit guard disables buttons.** Move the distinguishing value into a hidden input set on click. This applies to ANY multi-intent form (Save & add next / Save & done / Save & publish / etc.), not just camera flows.

## Nested template-literal pitfall (Bun/TS)

When building inline `<script>` strings inside a TS template literal, **nested backtick template literals inside the script body break the parser**:

```ts
// BROKEN — the inner `${url}` is parsed as TS interpolation, not as JS
return `<script>
  pending.innerHTML = items.map((f, i) => \`<img src="${f.url}" />\`).join('')
</script>`
```

Bun errors with `Expected ";" but found "class"` at the inner `<img`. Fix: use **string concatenation** inside the embedded JS, not template literals:

```ts
return `<script>
  pending.innerHTML = items.map((f, i) => '<img src="'+f.url+'" />').join('')
</script>`
```

Verified 2026-07-30 — booth `ui.ts` line 642 crashed the whole service on boot until this was fixed.

## Storage: photos go to R2 / disk, never git

- **R2** (Cloudflare object storage) or local disk on Zo — never commit inventory photos to git.
- GitHub is fine for site/code assets in a static site, but a **live inventory upload pipeline** (constant add/delete) bloats clones, breaks deploys, and hits LFS limits.
- Booth scale (~300–1000 photos @ 100–400 KB after compression) is trivial for R2 free tier (~10 GB headroom).

## Cloudflare deployment note (not static Pages)

A camera-upload inventory app is **not static HTML** — it needs a server (admin auth, write API, image upload endpoint). On Cloudflare free tier this means **Workers + D1 (data) + R2 (photos)**, not plain Pages. Pages Functions (Workers under the hood) also work. Plain static Pages cannot host this class of app.

## End-to-end verification checklist

Before declaring a camera-upload flow "done", verify on a real phone (or curl-driven E2E):

1. Login → cookie persists across restarts
2. Add item with **multiple** photos → all photos save (check DB row count, not just UI)
3. Public item page shows a **swipe gallery** with all photos
4. **Multi-intent save:** tap "Save & add next" → confirm the route lands on a fresh add form (not the dashboard). Check the redirect `Location` header, not just that it saved — the disabled-button bug makes "next" silently become "done".
5. Mark sold → item returns 404 on public, gone from gallery
6. Delete → item + photos removed
7. Restart service → items created this session still present (WAL checkpoint after writes)

The `form.get` vs `form.getAll` bug specifically passes step 2's UI check and only fails the DB count check — so always check the DB, not the browser. The disabled-button-drops-intent bug passes step 4's "it saved" check and only fails the redirect-target check — so always assert the `Location` header.
