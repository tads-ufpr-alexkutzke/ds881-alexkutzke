#!/usr/bin/env python3
"""
DevMarket — Scoreboard Generator

Generates an HTML scoreboard from a GitHub repository showing per-week
engagement scores and cumulative totals for each student.

Each week runs from Wednesday 21:00 BRT to the following Wednesday 21:00 BRT.
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests


# ── Constants ────────────────────────────────────────────────────────────────
BRT = timezone(timedelta(hours=-3))  # Brasília time (UTC-3)

# Scoring rules
WEEKLY_ENGAGEMENT_POINTS = 1.0    # max per week
LEADERSHIP_BONUS = 2.0             # one-time, if student has a fixed role
TECH_LEAD_ROLE = "Tech Lead Frontend"
PO_SM_ROLES = {"Product Owner", "Scrum Master"}
GRACE_PERIOD = timedelta(hours=2)

# Qualitative Participation Weights (Final Prize)
WEIGHT_PR_INFRA = 2.0        # DevOps, CI, Docker, Tests
WEIGHT_PR_DEFAULT = 1.0      # Standard features
WEIGHT_PR_DOCS = 0.2         # README, CONTRIBUTORS, typos
WEIGHT_REVIEW_FEEDBACK = 1.5 # Reviews with comments (> 20 chars)
WEIGHT_REVIEW_EMPTY = 0.5    # Just approval or very short comment

# DevOps rotation mapping (Week index -> Active Group)
DEVOPS_ROTATION = {
    0: "Grupo A",
    1: "Grupo B",
    2: "Grupo C",
    3: "Grupo D"
}

DEFAULT_TOTAL_WEEKS = 16
DEFAULT_STUDENTS_FILE = "alunos.csv"
DEFAULT_OUTPUT_FILE = "Placar.html"


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate DevMarket engagement scoreboard from GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Examples:
  python generate_scoreboard.py \\
      --repo "ds881-2026-alexkutzke/ds881-devmarket-2026-1-n" \\
      --start "2026-05-06T21:00:00-03:00"

  python generate_scoreboard.py \\
      -r "owner/repo" -s "2026-01-14T21:00:00-03:00" \\
      -i students.csv -o score.html -w 14
""",
    )
    parser.add_argument(
        "-r", "--repo",
        required=True,
        help="GitHub repository (owner/name), e.g. 'ds881-2026-alexkutzke/ds881-devmarket-2026-1-n'",
    )
    parser.add_argument(
        "-s", "--start",
        required=True,
        help="Project start datetime in ISO 8601, e.g. '2026-05-06T21:00:00-03:00' (BRT=UTC-3)",
    )
    parser.add_argument(
        "-w", "--weeks",
        type=int,
        default=DEFAULT_TOTAL_WEEKS,
        help=f"Total weeks to generate (default: {DEFAULT_TOTAL_WEEKS})",
    )
    parser.add_argument(
        "-i", "--students",
        default=DEFAULT_STUDENTS_FILE,
        help=f"Path to students CSV file (default: {DEFAULT_STUDENTS_FILE})",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output HTML file (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch to query commits from (default: main)",
    )
    parser.add_argument(
        "--no-participation",
        action="store_true",
        help="Disable participation points calculation and podium (useful for classes without prize)",
    )
    return parser.parse_args(argv)


def parse_project_start(raw: str):
    """Parse a user-supplied ISO 8601 datetime into a timezone-aware datetime
    and convert it to BRT."""
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid --start datetime '{raw}': {exc}") from exc
    if dt.tzinfo is None:
        raise SystemExit(
            f"--start datetime '{raw}' has no timezone. "
            "Use ISO 8601 with offset, e.g. '2026-05-06T21:00:00-03:00'"
        )
    return dt.astimezone(BRT)


def validate_repo(raw: str):
    parts = raw.split("/")
    if len(parts) != 2 or not all(parts):
        raise SystemExit(f"Invalid --repo format '{raw}'. Expected 'owner/name'.")
    return raw


# ── Week generation ─────────────────────────────────────────────────────────

def generate_weeks(project_start: datetime, num_weeks: int):
    """Generate *num_weeks* week boundaries anchored on *project_start* (in BRT).
    The transition point between weeks is shifted by GRACE_PERIOD (2 hours).
    """
    weeks = []
    for i in range(num_weeks):
        # Week 1 starts at project_start.
        # Subsequent weeks start at (project_start + i weeks) + GRACE_PERIOD.
        start = project_start + timedelta(weeks=i)
        if i > 0:
            start += GRACE_PERIOD
            
        # All weeks end at (project_start + (i+1) weeks) + GRACE_PERIOD.
        end = project_start + timedelta(weeks=i + 1) + GRACE_PERIOD
        
        weeks.append({
            "name": f"Semana {i + 1}",
            "start": start,
            "end": end,
            "start_str": start.strftime("%d/%m"),
            "end_str": end.strftime("%d/%m %H:%M"),
        })
    return weeks


def active_weeks(weeks, now=None):
    """Return weeks whose *start* ≤ *now* (in BRT)."""
    if now is None:
        now = datetime.now().astimezone(BRT)
    return [w for w in weeks if w["start"] <= now]


# ── GitHub API helpers ──────────────────────────────────────────────────────

def _github_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_github_data(repo: str, endpoint: str, params: dict | None = None):
    """Paginated fetch from GitHub REST API."""
    url = f"https://api.github.com/repos/{repo}/{endpoint}"
    headers = _github_headers()

    all_data = []
    page = 1
    while True:
        p = (params or {}) | {"page": page, "per_page": 100}
        try:
            resp = requests.get(url, headers=headers, params=p, timeout=30)
        except requests.RequestException as exc:
            print(f"Network error fetching {url}: {exc}")
            break
        if resp.status_code != 200:
            print(f"Error fetching {url}: HTTP {resp.status_code}")
            break
        data = resp.json()
        if not data:
            break
        all_data.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_data


def parse_github_datetime(iso_str: str):
    """Parse a GitHub UTC datetime string (ends with 'Z') into a BRT datetime."""
    return (
        datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=timezone.utc)
        .astimezone(BRT)
    )


def _safe_parse_github_dt(iso_str):
    """Parse without raising — returns None on failure."""
    try:
        return parse_github_datetime(iso_str)
    except (ValueError, TypeError):
        return None


def _utc_iso(ts: datetime):
    """Format a BRT datetime as UTC ISO for GitHub API *since* parameter."""
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Data fetching ───────────────────────────────────────────────────────────

def fetch_all_prs(repo: str):
    return fetch_github_data(repo, "pulls", {"state": "all", "sort": "created", "direction": "desc"})


def fetch_reviews(repo: str, pr_number: int):
    return fetch_github_data(repo, f"pulls/{pr_number}/reviews")


def fetch_commits(repo: str, branch: str, since: datetime):
    return fetch_github_data(
        repo, "commits", {"sha": branch, "since": _utc_iso(since)},
    )


def fetch_issues(repo: str, since: datetime):
    return fetch_github_data(
        repo, "issues", {"state": "all", "since": _utc_iso(since)},
    )


def fetch_path_commits(repo: str, path: str, since: datetime):
    """Fetch commits that touched a specific path since a given date."""
    return fetch_github_data(
        repo, "commits", {"path": path, "since": _utc_iso(since)},
    )


def fetch_pr_files(repo: str, pr_number: int):
    """Fetch the list of files changed in a pull request."""
    return fetch_github_data(repo, f"pulls/{pr_number}/files")


# ── Scoring ─────────────────────────────────────────────────────────────────

def _get_pr_weight(pr: dict, repo: str):
    """Determine qualitative weight of a PR based on its content/title."""
    title = pr.get("title", "").upper()
    
    # 1. Check by title/labels keywords (fast)
    infra_keywords = {"CI", "DOCKER", "WORKFLOW", "PIX", "INFRA", "PIPELINE", "TEST", "ARCHITECT"}
    docs_keywords = {"DOCS", "README", "CONTRIBUTORS", "TYPO"}
    
    if any(k in title for k in infra_keywords):
        return WEIGHT_PR_INFRA
    if any(k in title for k in docs_keywords):
        return WEIGHT_PR_DOCS
        
    # 2. Check by files (requires extra API call, only if title is ambiguous)
    try:
        files = fetch_pr_files(repo, pr["number"])
        filenames = [f["filename"] for f in files]
        
        if any(f.startswith(".github/") or "Dockerfile" in f or "docker-compose" in f for f in filenames):
            return WEIGHT_PR_INFRA
        if all(f.endswith(".md") for f in filenames):
            return WEIGHT_PR_DOCS
    except Exception:
        pass # Fallback to default if API fails

    return WEIGHT_PR_DEFAULT


def _get_review_weight(review: dict):
    """Determine qualitative weight of a review based on comment length."""
    body = (review.get("body") or "").strip()
    if len(body) > 20:
        return WEIGHT_REVIEW_FEEDBACK
    return WEIGHT_REVIEW_EMPTY


def _parse_commit_date(commit: dict):
    """Extract commit date string safely from a GitHub commit object."""
    try:
        return commit["commit"]["author"]["date"]
    except (KeyError, TypeError):
        return None


def _is_in_week(dt, week):
    """Check whether BRT datetime *dt* falls inside *week*."""
    return dt is not None and week["start"] <= dt < week["end"]


def calculate_scores(students, all_prs, all_commits, all_issues, weeks, repo: str, contrib_usernames: set, show_participation: bool = True):
    """Compute per-week and cumulative scores for every student."""
    # Index issues by creator (exclude PR entries returned by GitHub's issues API)
    user_issues: dict[str, list] = {}
    for issue in all_issues:
        if "pull_request" in issue:
            continue
        creator = issue["user"]["login"].lower()
        user_issues.setdefault(creator, []).append(issue)

    # Index PRs by author
    user_prs: dict[str, list] = {}
    for pr in all_prs:
        author = pr["user"]["login"].lower()
        user_prs.setdefault(author, []).append(pr)

    # Index reviews by reviewer
    user_reviews: dict[str, list] = {}
    print("Fetching reviews from GitHub…")
    for pr in all_prs:
        try:
            for r in fetch_reviews(repo, pr["number"]):
                user_info = r.get("user")
                if user_info is None:
                    continue  # ghost / deleted user
                reviewer = user_info["login"].lower()
                user_reviews.setdefault(reviewer, []).append(r)
        except Exception as exc:
            print(f"  Error fetching reviews for PR #{pr.get('number', '?')}: {exc}")

    scoreboard = []
    for student in students:
        username = student["github"].lower() if student["github"] else None

        # Students without GitHub handle get 0 everywhere
        if not username:
            scoreboard.append({
                "name": student["name"],
                "github": "N/A",
                "devops_group": student["devops_group"],
                "role": student["fixed_role"] or "Desenvolvedor",
                "weekly_scores": [],
                "cumulative": 0.0,
                "participation_points": 0.0,
                "details": "Usuário GitHub não informado",
            })
            continue

        fixed_role = student["fixed_role"]
        student_devops_group = student["devops_group"]
        is_tech_lead = fixed_role == TECH_LEAD_ROLE
        is_po_sm = fixed_role in PO_SM_ROLES if fixed_role else False
        is_devops = student_devops_group.strip().upper() == "GRUPO A"

        # One-time bonuses
        leadership_bonus = LEADERSHIP_BONUS if fixed_role else 0.0

        # CONTRIBUTORS.md task — checked in the first week (or by path commits)
        contrib_done = username in contrib_usernames

        # Global metrics
        merged_prs = [
            pr for pr in user_prs.get(username, [])
            if pr.get("merged_at") is not None
        ]
        num_merged = len(merged_prs)

        # Technical Obligation (2.0 pts): 2 merged PRs + 2 reviews
        student_reviews = user_reviews.get(username, [])
        total_reviews = len(student_reviews)
        tech_obligation_done = num_merged >= 2 and total_reviews >= 2
        tech_obligation_points = 2.0 if tech_obligation_done else 0.0

        # High Productivity bonus (0.5 pts): > 4 issues closed (approximated by merged PRs)
        high_prod_bonus = 0.5 if num_merged > 4 else 0.0
        
        # PO/SM alert — no issues at all across all time
        po_sm_has_issues = bool(user_issues.get(username)) if is_po_sm else False

        # ── Per-week scores ──────────────────────────────────────────────
        weekly_scores = []

        for i, week in enumerate(weeks):
            active_devops_group = DEVOPS_ROTATION.get(i, "N/A")
            is_devops_this_week = student_devops_group == active_devops_group

            ws_start, ws_end = week["start"], week["end"]
            week_score = 0.0
            week_engaged = False
            week_details = []

            # PRs opened (CONTRIBUTORS PR only counts in the first week)
            prs_in_week = 0
            for pr in user_prs.get(username, []):
                if _is_in_week(_safe_parse_github_dt(pr.get("created_at")), week):
                    is_contrib = "CONTRIBUTORS" in pr.get("title", "").upper()
                    if not is_contrib or i == 0:
                        prs_in_week += 1

            if prs_in_week:
                week_engaged = True
                week_details.append(f"{prs_in_week} PR(s)")

            # Reviews submitted
            reviews_in_week = sum(
                1 for r in student_reviews
                if _is_in_week(_safe_parse_github_dt(r.get("submitted_at")), week)
            )
            if reviews_in_week:
                week_engaged = True
                week_details.append(f"{reviews_in_week} review(s)")

            # DevOps commits (applies to student in their active week)
            if is_devops_this_week:
                commits_in_week = sum(
                    1 for c in all_commits
                    if c.get("author")
                    and c["author"]["login"].lower() == username
                    and _is_in_week(
                        _safe_parse_github_dt(_parse_commit_date(c)),
                        week,
                    )
                )
                if commits_in_week:
                    week_engaged = True
                    week_details.append(f"{commits_in_week} commits DevOps")

            # PO/SM issues created
            if is_po_sm:
                issues_in_week = sum(
                    1 for iss in user_issues.get(username, [])
                    if _is_in_week(_safe_parse_github_dt(iss.get("created_at")), week)
                )
                if issues_in_week:
                    week_engaged = True
                    week_details.append(f"{issues_in_week} issue(s) gestão")

            if week_engaged:
                # Cap weekly engagement at 1.0 point as per specification 13.1
                week_score = min(WEEKLY_ENGAGEMENT_POINTS, 1.0)
                details_str = " | ".join(week_details)
            else:
                details_str = "Sem engajamento"

            weekly_scores.append({
                "score": week_score,
                "engaged": week_engaged,
                "details": details_str,
            })

        # ── Cumulative (Scoreboard ranking) ──────────────────────────────
        weekly_total = sum(ws["score"] for ws in weekly_scores)
        cumulative = (
            weekly_total + 
            tech_obligation_points + high_prod_bonus
        )

        # Qualitative Participation Points (Final Prize)
        # Weighted PRs + Weighted Reviews
        participation_points = 0.0
        if show_participation:
            for pr in merged_prs:
                participation_points += _get_pr_weight(pr, repo)
            for r in student_reviews:
                participation_points += _get_review_weight(r)

        # ── Details string ───────────────────────────────────────────────
        all_details = []

        # Participation Breakdown
        if show_participation:
            all_details.append(f"🏆Partic Qualitativa: {participation_points:.1f} pts (PRs ponderados + Reviews c/ feedback)")

        # Technical Obligation tag
        tech_tag = "✅" if tech_obligation_done else "❌"
        all_details.append(f"🛠️Técnica {tech_tag}")

        # Compact per-week summary
        week_summaries = []
        for i, ws in enumerate(weekly_scores):
            score_str = f"{ws['score']:.1f}" if ws["score"] > 0 else "0"
            marker = "✅" if ws["engaged"] else "❌"
            week_summaries.append(f"S{i+1}:{marker}{score_str}")
        all_details.append(" ".join(week_summaries))

        # CONTRIBUTORS check: show ✅ for everyone who did it, ❌ only for non-exempt
        if contrib_done:
            all_details.append("📋CONTRIBUTORS ✅")
        elif not is_tech_lead and not is_devops:
            all_details.append("📋CONTRIBUTORS ❌")

        # Leadership bonus
        if fixed_role:
            all_details.append(f"👑liderança +{leadership_bonus:.0f} (apenas para nota)")

        # High Productivity bonus
        if high_prod_bonus > 0:
            all_details.append(f"🚀produtividade +{high_prod_bonus:.1f}")

        # PO/SM alert
        if is_po_sm and not po_sm_has_issues:
            all_details.append("<span style='color:orange'>⚠️ PO/SM sem issues</span>")

        scoreboard.append({
            "name": student["name"],
            "github": username,
            "devops_group": student["devops_group"],
            "role": fixed_role or "Desenvolvedor",
            "weekly_scores": weekly_scores,
            "cumulative": cumulative,
            "participation_points": participation_points,
            "details": " | ".join(all_details),
        })

    return scoreboard


# ── HTML generation ─────────────────────────────────────────────────────────

def _to_brt_now_str():
    return datetime.now().astimezone(BRT).strftime("%d/%m/%Y %H:%M BRT")


def generate_html(scoreboard, weeks_for_display, project_start: datetime, show_participation: bool = True):
    # Sort for the table (by Grade/Cumulative)
    scoreboard.sort(key=lambda x: x["cumulative"], reverse=True)

    # Top-3 for the podium
    if show_participation:
        podium_list = sorted(scoreboard, key=lambda x: x["participation_points"], reverse=True)
    else:
        podium_list = scoreboard[:3] # Default to grade if participation is hidden

    now_str = _to_brt_now_str()
    last_week = weeks_for_display[-1] if weeks_for_display else {"end_str": "—"}

    # Portuguese day of week names
    days_pt = [
        "segunda-feira", "terça-feira", "quarta-feira",
        "quinta-feira", "sexta-feira", "sábado", "domingo"
    ]
    deadline_dt = project_start + GRACE_PERIOD
    start_day_name = days_pt[deadline_dt.weekday()]

    # Table header
    table_headers = "<tr><th>Aluno</th><th>Grupo</th><th>Papel</th>"
    for w in weeks_for_display:
        table_headers += (
            f'<th title="{w["start_str"]} – {w["end_str"]}">{w["name"]}</th>'
        )
    
    if show_participation:
        table_headers += "<th>Nota</th><th>Partic.</th><th>Detalhes</th></tr>"
    else:
        table_headers += "<th>Nota Final</th><th>Detalhes</th></tr>"

    # Table body
    table_rows_parts = []
    for item in scoreboard:
        row = f"""\
                    <tr>
                        <td>{item['name']}<br><small><a href="https://github.com/{item['github']}" target="_blank">@{item['github']}</a></small></td>
                        <td><span class="devops-tag">{item['devops_group']}</span></td>
                        <td>{item['role']}</td>"""
        for ws in item["weekly_scores"]:
            cls = "score-good" if ws["score"] > 0 else "score-bad"
            row += f'<td class="{cls}" title="{ws["details"]}">{ws["score"]:.1f}</td>'
        
        row += f'<td class="score">{item["cumulative"]:.1f}</td>'
        
        if show_participation:
            row += f'<td class="score">{item["participation_points"]:.1f}</td>'
            
        row += f'<td class="details">{item["details"]}</td></tr>'
        table_rows_parts.append(row)
    table_rows = "\n".join(table_rows_parts)

    # Top-3 podium (only if participation is enabled)
    podium_html = ""
    if show_participation:
        podium_items_parts = []
        medals = [("first", "🥇"), ("second", "🥈"), ("third", "🥉")]
        for i, item in enumerate(podium_list[:3]):
            place, icon = medals[i]
            podium_items_parts.append(f"""\
                    <div class="ranking-item {place}">
                        <div style="font-size:2em;">{icon}</div>
                        <div style="font-weight:bold;">{item['name']}</div>
                        <div style="font-size:0.85em;color:#666;">{item['role']}</div>
                        <div class="score">{item['participation_points']:.1f} pts</div>
                    </div>""")
        podium_items = "\n".join(podium_items_parts)
        podium_html = f"""
        <div class="podium-title">🏅 Top Participação (Prêmio Final)</div>
        <div class="ranking">
{podium_items}
        </div>"""

    period_start = weeks_for_display[0]["start_str"] if weeks_for_display else "—"

    # Participation help text
    participation_help = ""
    disclaimer_premio = ""
    if show_participation:
        participation_help = f"""
            📌 <strong>Nota:</strong> Pontos para a disciplina (até {WEEKLY_ENGAGEMENT_POINTS:.1f} pt/semana + bônus técnicos).<br>
            📌 <strong>Partic.:</strong> Pontos Qualitativos para o Prêmio Final (PRs ponderados por impacto + Reviews com feedback técnico)."""
        
        disclaimer_premio = f"""
            <div style="margin-top:20px; padding:15px; background:#f9f9f9; border-left:4px solid #27ae60; text-align:left; font-size:0.85em;">
                <strong>Critérios de Pontuação Qualitativa (Prêmio Final):</strong><br>
                • <strong>PR de Infraestrutura ({WEIGHT_PR_INFRA} pts):</strong> Alterações em CI/CD, Docker, scripts de automação ou testes de arquitetura.<br>
                • <strong>PR de Feature ({WEIGHT_PR_DEFAULT} pts):</strong> Desenvolvimento de funcionalidades e lógica de negócio.<br>
                • <strong>PR de Documentação/Typo ({WEIGHT_PR_DOCS} pts):</strong> Ajustes em README, CONTRIBUTORS ou correções ortográficas.<br>
                • <strong>Review com Feedback ({WEIGHT_REVIEW_FEEDBACK} pts):</strong> Revisões com comentários técnicos ou sugestões de melhoria (>20 caracteres).<br>
                • <strong>Review Simples ({WEIGHT_REVIEW_EMPTY} pts):</strong> Aprovações sem comentários detalhados.
            </div>"""
    else:
        participation_help = f"📌 <strong>Nota Final:</strong> Pontos para a disciplina (até {WEEKLY_ENGAGEMENT_POINTS:.1f} pt/semana + bônus técnicos)."

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Placar DevMarket</title>
    <style>
        body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; background:#f4f7f6; color:#333; margin:0; padding:20px; }}
        .container {{ max-width:1300px; margin:auto; background:white; padding:30px; border-radius:8px; box-shadow:0 4px 6px rgba(0,0,0,.1); }}
        h1, h2 {{ color:#1c3d59; text-align:center; }}
        .ranking {{ display:flex; justify-content:space-around; margin-bottom:40px; background:#eef2f3; padding:20px; border-radius:8px; flex-wrap:wrap; gap:10px; }}
        .ranking-item {{ text-align:center; padding:10px; border-radius:8px; background:white; min-width:200px; box-shadow:0 2px 4px rgba(0,0,0,.05); }}
        .ranking-item.first {{ border:2px solid #ffd700; transform:scale(1.1); }}
        .ranking-item.second {{ border:2px solid #c0c0c0; }}
        .ranking-item.third {{ border:2px solid #cd7f32; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; font-size:.9em; }}
        th, td {{ padding:8px 10px; text-align:center; border-bottom:1px solid #ddd; }}
        th {{ background:#33495e; color:white; position:sticky; top:0; z-index:1; }}
        td:first-child, td:nth-child(2), td:nth-child(3) {{ text-align:left; }}
        tr:hover {{ background:#f1f1f1; }}
        .score {{ font-weight:bold; color:#27ae60; font-size:1.1em; }}
        .score-good {{ color:#27ae60; }}
        .score-bad {{ color:#e74c3c; }}
        .devops-tag {{ background:#e8eaed; padding:2px 8px; border-radius:4px; font-size:.8em; }}
        .footer {{ margin-top:30px; font-size:.8em; color:#777; text-align:center; }}
        .details {{ font-size:.78em; color:#666; max-width:320px; text-align:left; }}
        .period-info {{ text-align:center; color:#555; font-size:.9em; margin-bottom:10px; }}
        .table-wrap {{ overflow-x:auto; }}
        .week-subtitle {{ text-align:center; color:#777; font-size:.8em; margin-top:-10px; margin-bottom:20px; }}
        .podium-title {{ text-align:center; font-weight:bold; color:#1c3d59; margin-bottom:15px; font-size:1.2em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 DevMarket — Placar de Engajamento</h1>
        <p class="period-info">Período: {period_start} a {last_week["end_str"]} | Encerra {start_day_name} às {deadline_dt.strftime("%H:%M")} BRT</p>

        {podium_html}

        <div class="table-wrap">
            <table>
                <thead>
                    {table_headers}
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div class="week-subtitle">
            {participation_help}
            {disclaimer_premio}
        </div>

        <div class="footer">
            Gerado em: {now_str} | Regras CALMS<br>
            <strong>Aviso:</strong> O bônus de liderança (+{LEADERSHIP_BONUS:.0f}) é contabilizado apenas na nota final da disciplina e não aparece neste placar.
        </div>
    </div>
</body>
</html>"""


# ── Student parser ──────────────────────────────────────────────────────────

def parse_students_from_csv(file_path: str):
    students = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Nome", "").strip()
            # If name is empty, skip (handles empty lines or ,,,)
            if not name:
                continue

            github = row.get("Usuário github", "").strip()
            devops_group = row.get("Grupo DevOps", "").strip()
            fixed_role = row.get("Role Fixa", "").strip()

            students.append({
                "name": name,
                "github": github,
                "devops_group": devops_group,
                "fixed_role": fixed_role if fixed_role else None,
            })
    return students


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()

    # Validate & convert inputs
    repo = validate_repo(args.repo)
    project_start = parse_project_start(args.start)

    # Students
    if not os.path.exists(args.students):
        raise SystemExit(f"Students file not found: {args.students}")
    students = parse_students_from_csv(args.students)
    print(f"Students loaded: {len(students)}")

    # Weeks
    all_weeks = generate_weeks(project_start, args.weeks)
    weeks = active_weeks(all_weeks)
    if not weeks:
        raise SystemExit("No active weeks found (project hasn't started yet?).")
    print(
        f"Active weeks: {len(weeks)} ({weeks[0]['name']} a {weeks[-1]['name']})"
    )
    print(
        f"Week boundaries: {weeks[0]['start'].strftime('%a %d/%m %H:%M')} → "
        f"{weeks[-1]['end'].strftime('%a %d/%m %H:%M')} BRT"
    )

    # Fetch GitHub data
    try:
        print(f"Fetching data from GitHub repo '{repo}'…")
        prs = fetch_all_prs(repo)
        commits = fetch_commits(repo, args.branch, project_start)
        issues = fetch_issues(repo, project_start)
        
        # Robust CONTRIBUTORS.md check
        contrib_commits = fetch_path_commits(repo, "CONTRIBUTORS.md", project_start)
        contrib_usernames = {
            c["author"]["login"].lower() 
            for c in contrib_commits 
            if c.get("author") and c["author"].get("login")
        }

        print(f"  PRs: {len(prs)} | Commits: {len(commits)} | Issues: {len(issues)} | Contributors: {len(contrib_usernames)}")
    except Exception as exc:
        print(f"Error fetching GitHub data: {exc}. Using empty data.")
        prs = []
        commits = []
        issues = []
        contrib_usernames = set()

    # Score
    show_participation = not args.no_participation
    scoreboard = calculate_scores(students, prs, commits, issues, weeks, repo, contrib_usernames, show_participation=show_participation)

    # Output
    html = generate_html(scoreboard, weeks, project_start, show_participation=show_participation)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Scoreboard generated: {args.output}")
