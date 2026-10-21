# tilt-bot

A Python job-application assistant for Greenhouse job boards. It finds recently posted jobs that match the positions you're looking for, scores each one against the skills on your resume, and (in progress) fills out the application for you to review and submit yourself.

Nothing is ever submitted automatically. You check every application and click Submit.

## How it works

```
positions.txt + companies.txt
        │
        ▼
search_positions.py ──► jobs.txt         open jobs matching your positions, location, and age
        │
        ▼
rate_jobs.py ─────────► ratings.csv      every job scored against skills.txt
                        top_jobs.txt     jobs scoring MIN_SCORE or higher
        │
        ▼
bot.py (in progress) ─► fills each application, attaches your resume, waits for you to submit
```

Job data comes from Greenhouse's public [Job Board API](https://developers.greenhouse.io/job-board.html), which needs no account or key.

## Setup

Requires Python 3.10+ and Git Bash (on Windows).

```bash
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install anthropic playwright pydantic pyyaml python-docx
playwright install chromium
```

Run `source .venv/Scripts/activate` again in every new terminal.

Copy the example profile and fill in your own details:

```bash
cp user/profile.example.yaml profile.yaml
```

## Configuration

| File | What goes in it |
|---|---|
| `positions.txt` | Job titles to look for, one per line. A job matches if its title **contains** the line, so `support engineer` matches "Senior Support Engineer". |
| `companies.txt` | Greenhouse board tokens, one per line. The token is the name in the job URL: `job-boards.greenhouse.io/<token>/jobs/123`. |
| `skills.txt` | Skills and tools from your resume, one per line. Used to score jobs. |
| `dealbreakers.txt` | Phrases that rule a job out (e.g. `security clearance`). Each one lowers a job's score. |
| `profile.yaml` | Your contact info and standard answers for application forms. Not committed. See `user/profile.example.yaml`. |

Settings at the top of the scripts:

| Setting | File | Default | Meaning |
|---|---|---|---|
| `LOCATIONS` | `search_positions.py` | US + a few cities | Job location must contain one of these. `[]` allows any location. |
| `MAX_AGE_HOURS` | `search_positions.py` | `336` (14 days) | Only jobs first published within this many hours. |
| `USE_SEARCH` | `search_positions.py` | `False` | `True` uses Claude web search to discover new companies (needs Anthropic API credits). |
| `MY_YEARS` | `rate_jobs.py` | `8` | Your years of experience. Jobs asking for more lose points. |
| `MIN_SCORE` | `rate_jobs.py` | `30` | Score needed to make `top_jobs.txt`. |

## Usage

```bash
python search_positions.py   # find new matching jobs → jobs.txt
python -u rate_jobs.py       # score them → ratings.csv, top_jobs.txt
```

`search_positions.py` only adds jobs that aren't already in `jobs.txt`, so it's safe to run daily.

### How jobs are scored

| Rule | Points |
|---|---|
| Each skill from `skills.txt` mentioned in the posting | +10 |
| Each dealbreaker mentioned in the posting | −25 |
| Each year of required experience above `MY_YEARS` | −5 |

Matching is whole-word and case-insensitive.

## Finding companies

Greenhouse has no API for searching across companies, so `companies.txt` is built by hand (or with `USE_SEARCH = True`). Search Google for:

```
site:job-boards.greenhouse.io "support engineer"
```

and add the token from each result's URL. A `404` for a company means it doesn't use Greenhouse; remove it from the list.

## Privacy

`profile.yaml`, resumes, `applied.csv`, and the generated job lists are in `.gitignore`. Keep API keys in your shell profile (`~/.bashrc`), never in this repo.

## Roadmap

- [x] Find matching jobs through the Greenhouse API
- [x] Filter by location and posting age
- [x] Score jobs against resume skills
- [ ] `tailor_resume.py`: build a resume for each job that puts the most relevant experience first
- [ ] `bot.py`: fill the application form in a visible browser for the user to review and submit
- [ ] Lever job board support
