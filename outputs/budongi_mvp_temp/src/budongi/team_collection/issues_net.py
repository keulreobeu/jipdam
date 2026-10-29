"""Read-only, unauthenticated search of the team's GitHub [수집] issues (COLLECT-001 overlap check)."""
from __future__ import annotations

import json
import re
import urllib.request

from .contract import USER_AGENT, ContractError

API = "https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}"
DEFAULT_REPO = "keulreobeu/jipdam"


def fetch_issues(repo: str = DEFAULT_REPO, *, opener=None, max_pages: int = 20) -> list:
    """All issues and PRs (they share one number sequence), newest first, without credentials."""
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ContractError("invalid_repo")
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}))
    items = []
    for page in range(1, max_pages + 1):
        request = urllib.request.Request(API.format(repo=repo, page=page),
                                         headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
        try:
            with opener.open(request, timeout=30) as response:
                batch = json.loads(response.read(8 * 1024 * 1024).decode("utf-8"))
        except Exception:
            raise ContractError("github_unreachable") from None
        if not isinstance(batch, list):
            raise ContractError("github_unexpected_response")
        for issue in batch:
            items.append({"number": issue.get("number"), "title": issue.get("title") or "",
                          "state": issue.get("state"), "body": issue.get("body") or "",
                          "is_pr": "pull_request" in issue,
                          "labels": [label.get("name") for label in issue.get("labels") or []]})
        if len(batch) < 100:
            break
    return items


def tokens_for(source: dict) -> set:
    """Search tokens: the provider dataset ID (e.g. OA-15067, 15083033) and declared service names."""
    tokens = {str(source.get("dataset_id") or "").strip()}
    tokens.update(str(t).strip() for t in source.get("search_tokens", []))
    return {t for t in tokens if len(t) >= 4}


def find_overlaps(source: dict, issues: list) -> list:
    tokens = tokens_for(source)
    hits = []
    for issue in issues:
        text = f"{issue['title']}\n{issue['body']}"
        matched = sorted(t for t in tokens if t in text)
        if matched:
            hits.append({"number": issue["number"], "title": issue["title"], "state": issue["state"],
                         "is_pr": issue["is_pr"], "tokens": matched})
    return hits


def next_number(issues: list) -> int:
    return max((i["number"] for i in issues if isinstance(i.get("number"), int)), default=0) + 1
