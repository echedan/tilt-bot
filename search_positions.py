import json
import os
import re
import urllib.parse
import urllib.request
import anthropic
from datetime import datetime, timedelta, timezone

client = anthropic.Anthropic()

#Setup and helpers

LOCATIONS = ["united states", "remote", "michigan", "chicago", "boston", "ohio"] #empty list [] means all locations
MAX_AGE_HOURS = 336  # only jobs posted in the last 336 hours

GH_TOKEN = re.compile(r"greenhouse\.io/([a-z0-9_-]+)", re.I)
NOT_TOKENS = {"v1", "embed"}

def read_list(path):
    try:
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)

POSITIONS = [p.lower() for p in read_list("positions.txt")]

#Stage 1, find companies hiring each position

USE_SEARCH = False # True = Claude finds companies (needs API credits)

def find_companies(position):
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=4000,
        output_config={"effort": "low"},
        tools=[{
            "type": "web_search_20260209",
            "name": "web_search",
            "max_uses": 3,
            "allowed_domains": ["greenhouse.io"],   # only search Greenhouse
        }],
        messages=[{
            "role": "user",
            "content": f'Search for open "{position}" job postings on Greenhouse. '
                       f'Just run the searches; no summary needed.',
        }],
    )

    print("  stop_reason:", response.stop_reason)
    for block in response.content:
        print("  block:", block.type)
        if block.type == "web_search_tool_result":
            if isinstance(block.content, list):
                for r in block.content:
                    print("    url:", r.url)
            else:
                print("    search error:", block.content)


    tokens = set()
    for block in response.content:
        # Search results come back as their own blocks with real URLs in them
        if block.type == "web_search_tool_result" and isinstance(block.content, list):
            for result in block.content:
                m = GH_TOKEN.search(result.url)
                if m and m.group(1).lower() not in NOT_TOKENS:
                    tokens.add(m.group(1).lower())
    return tokens


#Stage 2, ask Greenhouse for matching jobs

def is_recent(job):
    published = job.get("first_published")
    if not published:
        return False    # no date = can't tell, skip it
    posted = datetime.fromisoformat(published)
    return datetime.now(timezone.utc) - posted <= timedelta(hours=MAX_AGE_HOURS)

def matching_jobs(token):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs")
    for job in data["jobs"]:
        title = job["title"].lower()
        location = job["location"]["name"].lower()
        if not any(p in title for p in POSITIONS):
            continue
        if LOCATIONS and not any(l in location for l in LOCATIONS):
            continue
        if not is_recent(job):
            continue
        yield job

# The search results are only used to find companies. Greenhouse is the source of truth for which jobs are actually open, so you don't get stale postings from an old search index.

#main()
def main():
    if not POSITIONS:
        print("positions.txt is empty")
        return

    #Stage 1, discover companies, remembering ones found on earlier runs
    companies = set(read_list("companies.txt"))
    before = len(companies)
    for position in (POSITIONS if USE_SEARCH else []):
        try:
            found = find_companies(position)
        except Exception as e:
            print(f"X search '{position}': {e}")
            continue
        print(f"'{position}': {len(found)} companies found")
        companies |= found

    with open("companies.txt", "w") as f:
        f.write("\n".join(sorted(companies)) + "\n")
    print(f"{len(companies) - before} new companies ({len(companies)} total)\n")

    #Stage 2, check every known company for matching open jobs

    seen = set(read_list("jobs.txt"))
    new = []
    for token in sorted(companies):
        print(f"checking {token}...")
        try:
            for job in matching_jobs(token):
                url = f"https://job-boards.greenhouse.io/{token}/jobs/{job['id']}"
                if url not in seen:
                    seen.add(url)
                    new.append(url)
                    print(f"+ {token}: {job['title']} ({job['location']['name']})")
        except Exception as e:
            print(f"X {token}: {e}")

    with open("jobs.txt", "a") as f:
        for url in new:
            f.write(url + "\n")
        print(f"\nAdded {len(new)} new jobs to jobs.txt")

if __name__ == "__main__":
    main()