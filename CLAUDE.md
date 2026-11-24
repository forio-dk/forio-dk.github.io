# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The GitHub Pages site `https://forio-dk.github.io` is the homepage for Forio's Android apps. Each app's source code
lives in a sibling repo:

| App | Repo | Application IDs | Policy here | Published URL (`privacyPolicyUrl`) |
|-----|------|-----------------|-------------|------------------------------------|
| Art Widget | `../art_widget` | `dk.forio.artwidget` | `artwidget/privacy-policy.md` | `https://forio-dk.github.io/artwidget/privacy-policy.html` |
| Atlas Hunt | `../atlas_hunt` | `dk.forio.atlashunt` | `atlashunt/privacy-policy.md` | `https://forio-dk.github.io/atlashunt/privacy-policy.html` |
| Stavebi, Syllabee, Складарик, Слогарик | `../learn_to_read` | `dk.forio.stavebi`, `.syllabee`, `.skladaryk`, `.slogarik` | `syllabee/privacy-policy.md` | `https://forio-dk.github.io/syllabee/privacy-policy.html` (one URL for all four flavours) |

Pushing to `main` publishes the site. Only the Art Widget home page has a build step and tests (see below); everything
else is published as it is.

## Policies are copies: edit them in the app repo

Each `<app>/privacy-policy.md` here is a verbatim copy of `docs/privacy-policy.md` in that app's repo. The copy in the
app repo is the source of truth, and the app repo's `/update-docs` command checks it against the code, the ads SDK
version and the Play Console answers. Make every change there first, then copy the whole file here. Don't edit a policy
here on its own.

To check that the copies match their sources (in Git Bash; `tr` strips CRLF line endings):

```bash
diff <(tr -d '\r' < ../art_widget/docs/privacy-policy.md)    <(tr -d '\r' < artwidget/privacy-policy.md)
diff <(tr -d '\r' < ../atlas_hunt/docs/privacy-policy.md)    <(tr -d '\r' < atlashunt/privacy-policy.md)
diff <(tr -d '\r' < ../learn_to_read/docs/privacy-policy.md) <(tr -d '\r' < syllabee/privacy-policy.md)
```

## How the site is served, and who depends on it

- **Jekyll is on.** The `.nojekyll` file was deleted on purpose. Jekyll is what turns `privacy-policy.md` into
  `privacy-policy.html`, and that `.html` URL is the one the apps' Settings screens and Play Console link to (it is
  `privacyPolicyUrl` in each app's `gradle.properties`). The `.md` URL is served as raw `text/markdown`.
- **Jekyll publishes every file it isn't told to skip.** Any file that isn't part of the site, such as this
  `CLAUDE.md`, goes in `exclude` in `_config.yml`. Leave `README.md` served: it is the policies' contact page.
- **Policy paths must not change.** Each policy also promises that new versions "will be published at this address".
- **`README.md`** holds the contact email and the list of apps. Every policy's **Contact** line links to
  `https://forio-dk.github.io/README.md`, where it is still served raw; keep it.
- **`index.html`** is the generated home page: a card per app, linking Art Widget's page and every app's privacy
  policy (Google's OAuth check wants the home page to link them). Atlas Hunt and Syllabee say "Coming soon", with no
  Google Play links, by the owner's decision.
- **The site root** is the developer website in Play Console and the home page on Atlas Hunt's OAuth consent screen.
- **`google3f02f6a48fbc475d.html`** verifies `https://forio-dk.github.io/` as a Search Console property. Atlas Hunt's
  OAuth branding verification needs it, so it must stay at the root unchanged (see `../atlas_hunt/docs/play-console.md`).
- **`app-ads.txt`** is the AdMob publisher declaration. AdMob reads it from the domain root for every app's ads.
- **`sitemap.xml` and `robots.txt`** at the root are generated with the Art Widget page; the sitemap lists its six
  language versions.

## Art Widget home page

`/artwidget/` (English) and `/artwidget/{da,it,ro,ru,uk}/` are a landing page that presents the app and links to
Google Play. They are generated; never edit them by hand.

- **Generator:** `python -X utf8 _build/artwidget/build.py` from the repo root (needs Jinja2, Pillow and ffmpeg; see
  `_build/artwidget/requirements.txt`). It reads `../art_widget/docs/listings/<listing>/graphics` and the en-US
  `video.mp4`, plus the committed downloads in `_build/artwidget/vendor/`, and writes only what changed: run it twice
  and `git status` stays clean. The video is re-encoded only when `artwidget/assets/video/` lacks it.
- **Tests:** `(cd _build/artwidget && python -X utf8 -m unittest -v)`. `tests/test_site.py` checks the committed
  output: links resolve, no third-party requests, hreflang is reciprocal, and `artwidget/privacy-policy.md` is
  untouched.
- **Edited by hand:** `_build/artwidget/template.html`, `_build/artwidget/strings/<code>.toml` (every language has
  English's keys; facts come from that language's store listing) and `artwidget/assets/site.css`.
- **Generated:** `artwidget/**/index.html`, `artwidget/assets/{img,badges,fonts,video}/`, the root `index.html`
  (from `_build/artwidget/home.html`), `favicon.ico`, `apple-touch-icon.png`, `sitemap.xml`, `robots.txt`.
- **The Forio logo** (a cream serif F hung in a gold frame on the navy wall) is drawn by `forio_mark()` in
  `_build/artwidget/assets.py` from the vendored Playfair Display TTF. The root `favicon.ico` and
  `apple-touch-icon.png` are what browsers show for every page that names no icon of its own, `README.md` and the
  policies included; the Art Widget pages keep Art Widget's icon.
- **`_build/` is never published:** Jekyll skips folders starting with `_`.
- **No third-party requests:** fonts, images, badges and video are served from `/artwidget/assets/`. Keep it so; the
  page advertises an app whose policy says it collects nothing itself.
- **Vendor downloads** (fonts, Google Play badges, the two Commons paintings) are fetched once by
  `_build/artwidget/fetch_vendor.py`, with their sources in `vendor/SOURCES.md`.

## Adding an app

1. Copy the app repo's `docs/privacy-policy.md` to `<app>/privacy-policy.md`.
2. Add the app's name to the list in `README.md`.
3. In the app repo's `gradle.properties`, set `privacyPolicyUrl=https://forio-dk.github.io/<app>/privacy-policy.html`.
