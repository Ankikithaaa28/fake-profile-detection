# Fake Profile Detection System

A Django web application that estimates how likely a social-media profile or email
address is to be fake. Pick a platform, enter a username or email, and get a verdict,
a risk meter, and a plain-English list of the reasons behind the score.

| Platform | Input | Data source |
|----------|-------|-------------|
| **Email** | address (provider dropdown or custom domain) | DNS (MX records), HTTP probe, built-in domain/keyword lists |
| **Instagram** | public username | [Instaloader](https://instaloader.github.io/) (public profile data) |
| **X (Twitter)** | public username | X API v2 via [Tweepy](https://www.tweepy.org/) |

The detection is **rule-based**: each platform checks a set of red flags and adds up a
score. It does not use a trained machine-learning model (see [Limitations](#limitations--future-work)).

---

## Live demo

**<https://fake-profile-detection-iota.vercel.app>**

No sign-up needed — pick a platform, enter a username or email and hit **Detect Now**.

| Page | URL |
|------|-----|
| Home | `/` |
| Email | `/email_page/` |
| Instagram | `/instagram_page/` |
| X (Twitter) | `/x_page/` |

Hosted on [Vercel](https://vercel.com), auto-deployed from this repository on every push
to `main`.

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS` are stored as Vercel
environment variables, so no secrets live in the repository.

---

## Quick start

Requires **Python 3.9 – 3.12**.

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
cd backend
python manage.py migrate
python manage.py runserver
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd backend
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

The **Email** and **Instagram** detectors work immediately. The **X** detector needs a
bearer token (below).

### X (Twitter) API key — optional

1. Create an app in the [X Developer Portal](https://developer.x.com) and copy its **Bearer Token**.
2. Paste it into `.env`:
   ```
   FAKEPROFILE_BEARER_TOKEN=your_token_here
   ```
3. Restart the server.

Without a token the rest of the site still runs and the X page shows a clear
"credentials not configured" message. What the X API lets you read depends on your
developer access tier, so test your key before a demo.

> `.env` is listed in `.gitignore`. Never commit real keys.

### Run the tests

```bash
cd backend
python manage.py test
```

The suite (48 tests) mocks DNS, HTTP, Instaloader and the X API, so it runs offline
and needs no credentials.

---

## How the scoring works

### Email — penalty points, normalised to a 0–100 % risk meter

Points are added for each risk signal, divided by an expected maximum of 45, and capped at 100 %.

| Signal | Points |
|--------|--------|
| Disposable-email domain (e.g. mailinator) | +10 |
| Unknown domain with a website / without one | +2 / +4 |
| Common but non-top-tier provider | +2 |
| Spam-associated TLD (`.xyz`, `.top`, `.loan` …) | +1 to +4 |
| No MX records (trusted provider / other) | +2 / +5 |
| Username: suspicious keyword | +6 |
| Username: gibberish / random-looking | +4 |
| Username: repeated or blacklisted pattern | +3 |
| Username: digits only | +3 |
| Username: odd length, unusual characters, too many symbols | +2 each |

Verdict: **≥ 75 %** very likely fake · **10 – 74 %** possibly suspicious · **< 10 %** looks legitimate.
Invalid formats score 100 %.

### Instagram — five checks, one point each

Posts (≥ 5) · sensible follower/following ratio · profile picture · bio of 10+ characters · full name present.

**5** = Genuine · **3 – 4** = Suspicious but Chill · **0 – 2** = Fake.
The meter shows *authenticity* (score × 20 %), so higher is better.

### X — five red flags, 20 points each (higher = more likely fake)

Default/missing profile picture · empty bio · under 10 followers while following 300+ ·
fewer than 10 tweets · account younger than 90 days.

Score **> 50** (three or more flags) = Fake Profile.

---

## Project structure

```
fake_profile_detection/
├── requirements.txt
├── .env.example              # copy to .env (never commit .env)
├── README.md
└── backend/
    ├── manage.py
    ├── fake_profile_backend/ # project settings, URLs, landing pages, visit counter
    ├── email_detector/       # email analysis (detection.py) + view + template
    ├── instagram/            # Instagram analysis (detection.py) + view + templates
    ├── x/                    # X analysis + view + template
    ├── templates/            # shared landing pages
    └── static/               # CSS, JS, icons
```

The SQLite database (`db.sqlite3`) is created in the project root by `migrate`.
It only stores per-platform page-visit counters; lookups are not saved.

---

## Limitations & future work

Being upfront about what this project is and isn't:

- **Heuristics, not machine learning.** Weights and thresholds are hand-picked and have
  not been validated against a labelled dataset, so there are no accuracy figures.
- **Email keyword matching is substring-based**, so genuine addresses containing words
  like `bot`, `test` or `temp` inside a name (e.g. *Abbott*, *contest*) can be flagged.
  A clean-looking address on a disposable domain scores ~22 % ("possibly suspicious")
  rather than "high risk". The tool checks the *domain* accepts mail, not that the mailbox exists.
- **Instagram** lookups are anonymous and Instagram frequently rate-limits or blocks
  them; the app reports this instead of crashing.
- **Meters differ by platform:** email and X show *fakeness*, Instagram shows *authenticity*.
- Only public profile data is analysed. Results are indicative, not proof — don't use
  them to accuse a real person.

Ideas for next steps:

- Train and evaluate a classifier (e.g. scikit-learn) on a labelled fake-account dataset
  and compare it to the rule-based score.
- Add behavioural features (posting cadence, follower growth, duplicate content).
- Unify the meters and verdict wording across platforms.
- Move off SQLite: Vercel's filesystem is read-only and ephemeral, so the visit
  counters reset on every deploy. A managed Postgres/Redis store would persist them.
