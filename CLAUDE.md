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

Pushing to `main` publishes the site. The home page, the Art Widget page and the site icons have a build step and tests
(see below); everything else is published as it is.

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
- **`index.html`** is the generated home page: a card per app, linking Art Widget's and Atlas Hunt's pages and every
  app's privacy policy (Google's OAuth check wants the home page to link them). Syllabee says "Coming soon", with no
  Google Play link, by the owner's decision.
- **The site root** is the developer website in Play Console and the home page on Atlas Hunt's OAuth consent screen.
- **`google3f02f6a48fbc475d.html`** verifies `https://forio-dk.github.io/` as a Search Console property. Atlas Hunt's
  OAuth branding verification needs it, so it must stay at the root unchanged (see `../atlas_hunt/docs/play-console.md`).
- **`app-ads.txt`** is the AdMob publisher declaration. AdMob reads it from the domain root for every app's ads.
- **`sitemap.xml` and `robots.txt`** at the root are generated; the sitemap lists the home page and the six language
  versions of the Art Widget and Atlas Hunt pages.

## Generated pages: the home page and the app pages

`/` is the site's home page. `/artwidget/` and `/atlashunt/` (English) and `/<app>/{da,it,ro,ru,uk}/` are landing pages
that present an app and link to Google Play. All of them are generated; never edit them by hand.

- **Generator:** `python -X utf8 _build/site/build.py` from the repo root (needs Jinja2, Pillow and ffmpeg; see
  `_build/site/requirements.txt`). It reads each app's store listings in its sibling repo (`../art_widget`,
  `../atlas_hunt`: `docs/listings/<listing>/graphics` and `video.mp4`) plus the committed downloads in
  `_build/site/vendor/`, and writes only what changed: run it twice and `git status` stays clean. A video is
  re-encoded only when its output is missing or the source video is newer.
- **Apps:** `config.py` describes each app with an `App` (slug, name, package, repo, theme colour, schema.org
  category, heading font); `artwidget.py` and `atlashunt.py` build their pages; `build.py` runs them, then the home
  page, sitemap and robots.txt.
- **Atlas Hunt's pictures:** each language's page shows its own listing's Play screenshots (`phone-2/3/4/5/6/8`),
  `feature-graphic.png` (the share image) and `video.mp4`; the level tiles use the en-US `leaderboard-*-512.png` icons
  (they have no text). The `home-N-<screen>.png` shots appear as the "A closer look" gallery on a page only when that
  page's listing has them (today en-US only), in N order. The build stops on a `home-*.png` not named that way
  (`<screen>` in lowercase letters, digits and hyphens), on two shots of the same screen, and on a screen without a
  caption in that language's `gallery.captions`; it deletes the images of shots no longer in the listing. Counted
  strings such as `gallery.sub` have a form per plural category (`plural.py`). Each shot opens enlarged in a popover (`popovertarget`, no script); the enlarged
  shot is a background image so that browsers fetch it only when it is opened.
- **Tests:** `(cd _build/site && python -X utf8 -m unittest -v)`. `tests/test_site.py` checks the committed
  output, the home page included: links resolve, no third-party requests, hreflang is reciprocal per app, and all
  three `privacy-policy.md` files are untouched (their git blobs are pinned).
- **Edited by hand:** `_build/site/base.html` and `macros.html` (what every app page shares: head, top bar, footer,
  the closing sections), `_build/site/apps/<app>/template.html` (each page's own sections),
  `_build/site/apps/<app>/strings/<code>.toml` (every language has English's keys; facts come from that language's
  store listing; translations made for a page end in `# new` until the owner reviews them), `_build/site/home.html`
  (the home page, English only; its card texts are the apps' en-US store short descriptions), `assets/site.css`
  (shared by all generated pages, with the colour tokens in `:root`) and each app's `<app>/assets/theme.css`.
- **Generated:** `<app>/**/index.html`, `<app>/assets/{img,video}/`, `assets/{fonts,badges,img}/`, the root
  `index.html` (from `_build/site/home.html`), `favicon.ico`, `apple-touch-icon.png`, `sitemap.xml`, `robots.txt`.
- **The Forio logo** (a cream serif F hung in a gold frame on the navy wall) is drawn by `forio_mark()` in
  `_build/site/assets.py` from the vendored Playfair Display TTF. The root `favicon.ico` and
  `apple-touch-icon.png` are what browsers show for every page that names no icon of its own, `README.md` and the
  policies included; each app's pages keep the app's icon.
- **`_build/` is never published:** Jekyll skips folders starting with `_`.
- **No third-party requests:** fonts, images, badges and videos are served from `/assets/` and `/<app>/assets/`. Keep
  it so; the pages advertise apps whose policies say they collect nothing themselves.
- **Vendor files** (fonts, Google Play badges, the two Commons paintings, and the Atlas Hunt and Syllabee icons copied
  from their repos) are fetched once by `_build/site/fetch_vendor.py`, with their sources in `vendor/SOURCES.md`.

## Adding an app

1. Copy the app repo's `docs/privacy-policy.md` to `<app>/privacy-policy.md`.
2. Add the app's name to the list in `README.md`.
3. In the app repo's `gradle.properties`, set `privacyPolicyUrl=https://forio-dk.github.io/<app>/privacy-policy.html`.
4. Add a card to `_build/site/home.html`, linking the new policy (the home page must link every app's policy),
   with the app's icon (add it to `LOCAL_VENDOR` in `_build/site/config.py` and run `fetch_vendor.py`). Update
   `HomeTest`'s expected headings and links, add the policy's blob to `POLICY_BLOBS` in `tests/test_site.py`, then
   rebuild.
5. Optionally give it a landing page like Art Widget's and Atlas Hunt's: an `App` in `config.py` (and in `APPS`),
   `_build/site/apps/<app>/template.html` extending `base.html`, its `strings/<code>.toml`, a builder module added to
   `BUILDERS` in `build.py`, and `<app>/assets/theme.css`.
