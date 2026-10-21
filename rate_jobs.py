import csv
import html
import json
import re
import time
import urllib.request

MY_YEARS = 8    # years of relevant experience
MIN_SCORE = 30  # jobs at or above this go to top_jobs.txt

URL_PARTS = re.compile(r"greenhouse\.io/([^/]+)/jobs/(\d+)")

def read_list(path):
    try:
        with open(path) as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return []

SKILLS = read_list("skills.txt")
DEALBREAKERS = read_list("dealbreakers.txt")

# Get a job's full description from its Greenhouse URL
def job_description(url):
    token, job_id = URL_PARTS.search(url).groups()
    api = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}"
    with urllib.request.urlopen(api, timeout=30) as resp:
        job = json.load(resp)

    # Greenhouse sends the description as escaped HTML: unescape, then strip tags
    text = re.sub(r"<[^>]+>", " ", html.unescape(job["content"]))
    return token, job["title"], job["location"]["name"], text.lower()

# Scoring rules
def has(phrase, text):
    # \b = whole word only, so "sql" doesn't match inside "mysqldump"
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

def years_required(text):
    nums = [int(n) for n in re.findall(r"(\d+)\+?\s*(?:or more\s+)?years", text)]
    nums = [n for n in nums if n <= 15] # ignore "founded 50 years ago"
    return max(nums, default=0)

def rate(text):
    matched = [s for s in SKILLS if has(s, text)]
    flags = [d for d in DEALBREAKERS if has(d, text)]
    years = years_required(text)

    score = len(matched) * 10   # +10 per skill you have
    score -= len(flags) * 25    # -25 per dealbreaker
    if years > MY_YEARS:
        score -= (years - MY_YEARS) * 5 # -5 per year over your experience
    return score, matched, flags, years

# main()
def main():
    urls = read_list("jobs.txt")
    results = []

    for i, url in enumerate(urls, 1):
        try:
            company, title, location, text = job_description(url)
        except Exception as e:
            print(f"[{i}/{len(urls)}] X {url}: {e}")    # 404 usually = job closed
            continue
        score, matched, flags, years = rate(text)
        results.append([score, title, company, location, years, ", ".join(matched), ", ".join(flags), url])

        print(f"[{i}/{len(urls)}] {score:>4} {title} @ {company}")
        time.sleep(0.2) # be polite to Greenhouse

    results.sort(reverse=True)  # highest score first

    with open("ratings.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["score", "title", "company", "location", "years_required", "skills_matched", "dealbreakers", "url"])
        w.writerows(results)

    top = [r for r in results if r[0] >= MIN_SCORE]
    with open("top_jobs.txt", "w") as f:
        for r in top:
            f.write(r[-1] + "\n")

    print(f"\nRated {len(results)} jobs. {len(top)} scored {MIN_SCORE}+ → top_jobs.txt")
    print("\nTop 10:")
    for r in results[:10]:
        print(f"    {r[0]:>4}   {r[1]} @ {r[2]}     [{r[5]}]")

if __name__ == "__main__":
    main()