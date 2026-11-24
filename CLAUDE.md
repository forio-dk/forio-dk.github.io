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

There is no build, lint or test step. Pushing to `main` publishes the site.

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
  `https://forio-dk.github.io/README.md`, and `index.html` redirects there.
- **The site root** is the developer website in Play Console and the home page on Atlas Hunt's OAuth consent screen.
- **`google3f02f6a48fbc475d.html`** verifies `https://forio-dk.github.io/` as a Search Console property. Atlas Hunt's
  OAuth branding verification needs it, so it must stay at the root unchanged (see `../atlas_hunt/docs/play-console.md`).
- **`app-ads.txt`** is the AdMob publisher declaration. AdMob reads it from the domain root for every app's ads.

## Adding an app

1. Copy the app repo's `docs/privacy-policy.md` to `<app>/privacy-policy.md`.
2. Add the app's name to the list in `README.md`.
3. In the app repo's `gradle.properties`, set `privacyPolicyUrl=https://forio-dk.github.io/<app>/privacy-policy.html`.
