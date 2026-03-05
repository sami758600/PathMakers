from __future__ import annotations

import argparse
import textwrap
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional

from flask import Flask, render_template, request


@dataclass
class OrganizationProfile:
    name: str
    org_type: str
    sectors: List[str]
    location: str
    years_operating: int
    has_501c3: bool
    annual_budget_usd: int
    team_size: int
    mission: str
    program_focus: str
    attachments: List[str]
    past_grants: List[str] = field(default_factory=list)


@dataclass
class GrantOpportunity:
    grant_id: str
    title: str
    source: str
    deadline: date
    eligible_org_types: List[str]
    sectors: List[str]
    geographies: List[str]
    min_years_operating: int
    requires_501c3: bool
    amount_min_usd: int
    amount_max_usd: int
    required_fields: List[str]
    required_attachments: List[str]
    priorities: List[str]
    word_limits: Dict[str, int]


@dataclass
class DiscoveryResult:
    grant: GrantOpportunity
    score: float
    reasons: List[str]


@dataclass
class ComplianceIssue:
    severity: str
    message: str


class DiscoveryEngine:
    def rank(
        self,
        profile: OrganizationProfile,
        grants: List[GrantOpportunity],
        top_n: int = 5,
    ) -> List[DiscoveryResult]:
        today = date.today()
        ranked: List[DiscoveryResult] = []

        for grant in grants:
            score = 0.0
            reasons: List[str] = []

            if profile.org_type in grant.eligible_org_types:
                score += 30
                reasons.append("org type eligible")
            else:
                score -= 100
                reasons.append("org type mismatch")

            overlap = len(
                set(s.lower() for s in profile.sectors)
                & set(s.lower() for s in grant.sectors)
            )
            if overlap:
                score += min(30, overlap * 15)
                reasons.append(f"sector overlap x{overlap}")
            else:
                score -= 10
                reasons.append("no sector overlap")

            geo_norm = [geo.lower() for geo in grant.geographies]
            if "global" in geo_norm or "us" in geo_norm or profile.location.lower() in geo_norm:
                score += 20
                reasons.append("geography match")
            else:
                score -= 10
                reasons.append("geography mismatch")

            if grant.requires_501c3:
                if profile.has_501c3:
                    score += 10
                    reasons.append("501(c)(3) satisfied")
                else:
                    score -= 100
                    reasons.append("requires 501(c)(3)")

            days_left = (grant.deadline - today).days
            if days_left < 0:
                score -= 60
                reasons.append("deadline passed")
            else:
                urgency_score = max(0.0, 20.0 - (days_left * 0.4))
                score += urgency_score
                reasons.append(f"deadline in {days_left} days")

            if profile.years_operating >= grant.min_years_operating:
                score += 10
                reasons.append("experience requirement met")
            else:
                score -= 20
                reasons.append("experience requirement not met")

            ranked.append(DiscoveryResult(grant=grant, score=round(score, 2), reasons=reasons))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_n]


class KnowledgeBase:
    def __init__(self, profile: OrganizationProfile) -> None:
        self.profile = profile

    def lookup(self, field_name: str) -> str:
        p = self.profile
        mapping = {
            "org_name": p.name,
            "org_type": p.org_type,
            "mission_statement": p.mission,
            "project_summary": p.program_focus,
            "location": p.location,
            "years_operating": str(p.years_operating),
            "annual_budget": f"${p.annual_budget_usd:,}",
            "team_size": str(p.team_size),
            "past_grants": ", ".join(p.past_grants) if p.past_grants else "None",
        }
        return mapping.get(field_name, "[NEEDS_INPUT]")


class AutoFillEngine:
    def fill_fields(self, grant: GrantOpportunity, kb: KnowledgeBase) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for name in grant.required_fields:
            if name == "requested_amount":
                suggested = int((grant.amount_min_usd + grant.amount_max_usd) / 2)
                fields[name] = f"${suggested:,}"
            else:
                fields[name] = kb.lookup(name)
        return fields


class NarrativeEngine:
    def generate(self, profile: OrganizationProfile, grant: GrantOpportunity) -> Dict[str, str]:
        priorities = ", ".join(grant.priorities)

        project_description = textwrap.dedent(
            f"""
            {profile.name} proposes a focused program aligned to {grant.title}.
            The initiative advances {profile.program_focus.lower()} and is designed for measurable progress in 12 months.
            This application is tailored to the funder's stated priorities: {priorities}.
            """
        ).strip()

        impact_statement = textwrap.dedent(
            """
            Our target beneficiaries are communities that currently have limited access to resources.
            The project tracks outcomes monthly and reports against clear KPIs, including participation, completion, and retention.
            We expect sustained impact by embedding delivery with existing local partners.
            """
        ).strip()

        budget_justification = textwrap.dedent(
            """
            Requested funds will support staffing, program delivery, monitoring, and compliance reporting.
            The budget is scoped to realistic implementation and includes a contingency buffer for procurement and operations.
            Internal controls and monthly financial reviews will ensure responsible fund utilization.
            """
        ).strip()

        return {
            "project_description": project_description,
            "impact_statement": impact_statement,
            "budget_justification": budget_justification,
        }


class ComplianceGuard:
    def validate(
        self,
        profile: OrganizationProfile,
        grant: GrantOpportunity,
        fields: Dict[str, str],
        narratives: Dict[str, str],
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []

        if profile.org_type not in grant.eligible_org_types:
            issues.append(ComplianceIssue("BLOCKER", "Organization type is not eligible."))

        if grant.requires_501c3 and not profile.has_501c3:
            issues.append(ComplianceIssue("BLOCKER", "Grant requires 501(c)(3) status."))

        if profile.years_operating < grant.min_years_operating:
            issues.append(
                ComplianceIssue(
                    "BLOCKER",
                    f"Minimum operating history is {grant.min_years_operating} years.",
                )
            )

        missing_field_values = [name for name, value in fields.items() if not value or value == "[NEEDS_INPUT]"]
        if missing_field_values:
            issues.append(
                ComplianceIssue(
                    "BLOCKER",
                    "Missing required field values: " + ", ".join(missing_field_values),
                )
            )

        missing_docs = [doc for doc in grant.required_attachments if doc not in profile.attachments]
        if missing_docs:
            issues.append(
                ComplianceIssue(
                    "BLOCKER",
                    "Missing required attachments: " + ", ".join(missing_docs),
                )
            )

        for key, limit in grant.word_limits.items():
            words = len(narratives.get(key, "").split())
            if words > limit:
                issues.append(
                    ComplianceIssue(
                        "WARNING",
                        f"{key} exceeds word limit ({words}/{limit}).",
                    )
                )

        if (grant.deadline - date.today()).days < 0:
            issues.append(ComplianceIssue("BLOCKER", "Deadline has already passed."))

        return issues


class GrantAgentPrototype:
    def __init__(self, profile: OrganizationProfile, grants: List[GrantOpportunity]) -> None:
        self.profile = profile
        self.grants = grants
        self.discovery = DiscoveryEngine()
        self.kb = KnowledgeBase(profile)
        self.autofill = AutoFillEngine()
        self.narrative = NarrativeEngine()
        self.compliance = ComplianceGuard()

    def execute(self, selected_grant_id: Optional[str] = None, auto_approve: bool = False) -> Dict[str, object]:
        ranked_results = self.discovery.rank(self.profile, self.grants, top_n=5)
        if not ranked_results:
            raise ValueError("No grants available to score.")

        selected_result = ranked_results[0]
        if selected_grant_id:
            for result in ranked_results:
                if result.grant.grant_id == selected_grant_id:
                    selected_result = result
                    break

        selected_grant = selected_result.grant
        fields = self.autofill.fill_fields(selected_grant, self.kb)
        narratives = self.narrative.generate(self.profile, selected_grant)
        compliance_issues = self.compliance.validate(self.profile, selected_grant, fields, narratives)

        blockers = [issue for issue in compliance_issues if issue.severity == "BLOCKER"]
        if blockers:
            status = "BLOCKED"
        elif auto_approve:
            status = "SUBMITTED"
        else:
            status = "DRAFT_REVIEW"

        return {
            "ranked_results": ranked_results,
            "selected_result": selected_result,
            "selected_grant": selected_grant,
            "fields": fields,
            "narratives": narratives,
            "compliance_issues": compliance_issues,
            "status": status,
        }


def sample_profile() -> OrganizationProfile:
    return OrganizationProfile(
        name="GreenBridge Collective",
        org_type="nonprofit",
        sectors=["climate", "education", "workforce"],
        location="US",
        years_operating=4,
        has_501c3=True,
        annual_budget_usd=420000,
        team_size=9,
        mission="We build climate-resilient skills and pathways for underserved communities.",
        program_focus="community climate workforce training with measurable local employment outcomes",
        attachments=["irs_501c3_letter", "annual_budget_sheet", "board_list", "impact_report"],
        past_grants=["City Green Skills 2024", "Climate Action Seed 2025"],
    )


def sample_grants() -> List[GrantOpportunity]:
    today = date.today()
    return [
        GrantOpportunity(
            grant_id="GR-1001",
            title="Community Climate Workforce Fund",
            source="Foundation",
            deadline=today + timedelta(days=18),
            eligible_org_types=["nonprofit", "research_institute"],
            sectors=["climate", "workforce", "education"],
            geographies=["US"],
            min_years_operating=2,
            requires_501c3=True,
            amount_min_usd=50000,
            amount_max_usd=150000,
            required_fields=[
                "org_name",
                "mission_statement",
                "project_summary",
                "years_operating",
                "annual_budget",
                "requested_amount",
            ],
            required_attachments=["irs_501c3_letter", "annual_budget_sheet", "board_list"],
            priorities=["equity", "job outcomes", "climate adaptation"],
            word_limits={
                "project_description": 140,
                "impact_statement": 120,
                "budget_justification": 120,
            },
        ),
        GrantOpportunity(
            grant_id="GR-1002",
            title="DeepTech Commercialization Grant",
            source="Federal",
            deadline=today + timedelta(days=41),
            eligible_org_types=["startup"],
            sectors=["ai", "deeptech"],
            geographies=["US"],
            min_years_operating=1,
            requires_501c3=False,
            amount_min_usd=100000,
            amount_max_usd=500000,
            required_fields=["org_name", "project_summary", "team_size", "requested_amount"],
            required_attachments=["annual_budget_sheet"],
            priorities=["commercial readiness", "innovation", "scalability"],
            word_limits={
                "project_description": 180,
                "impact_statement": 140,
                "budget_justification": 140,
            },
        ),
        GrantOpportunity(
            grant_id="GR-1003",
            title="Regional Inclusion Mini-Grant",
            source="Corporate CSR",
            deadline=today + timedelta(days=9),
            eligible_org_types=["nonprofit", "startup"],
            sectors=["education", "inclusion", "community"],
            geographies=["US", "global"],
            min_years_operating=0,
            requires_501c3=False,
            amount_min_usd=10000,
            amount_max_usd=30000,
            required_fields=["org_name", "project_summary", "location", "requested_amount"],
            required_attachments=["impact_report"],
            priorities=["access", "community participation", "execution speed"],
            word_limits={
                "project_description": 110,
                "impact_statement": 90,
                "budget_justification": 90,
            },
        ),
    ]


def split_csv(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def int_or_default(raw: str, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def profile_from_form(form_data) -> OrganizationProfile:
    return OrganizationProfile(
        name=form_data.get("name", "").strip() or "Prototype Org",
        org_type=form_data.get("org_type", "nonprofit").strip() or "nonprofit",
        sectors=split_csv(form_data.get("sectors", "")) or ["education"],
        location=form_data.get("location", "US").strip() or "US",
        years_operating=int_or_default(form_data.get("years_operating", "1"), 1),
        has_501c3=form_data.get("has_501c3") == "on",
        annual_budget_usd=int_or_default(form_data.get("annual_budget_usd", "100000"), 100000),
        team_size=int_or_default(form_data.get("team_size", "5"), 5),
        mission=form_data.get("mission", "").strip() or "Mission not provided.",
        program_focus=form_data.get("program_focus", "").strip() or "Program focus not provided.",
        attachments=split_csv(form_data.get("attachments", "")),
        past_grants=split_csv(form_data.get("past_grants", "")),
    )


def run_cli(auto_approve: bool) -> None:
    profile = sample_profile()
    grants = sample_grants()
    agent = GrantAgentPrototype(profile=profile, grants=grants)
    result = agent.execute(auto_approve=auto_approve)

    print("EvolveX Grant Agent Prototype")
    print("=" * 36)
    for idx, item in enumerate(result["ranked_results"], start=1):
        print(f"{idx}. {item.grant.grant_id} | {item.grant.title} | score {item.score}")

    print(f"\nSelected: {result['selected_grant'].grant_id}")
    print(f"Status: {result['status']}")


def generate_proposal_text(org: Dict[str, str], grant: Dict[str, str]) -> str:
    org_name = org.get("name", "Your Organization")
    org_type = org.get("type", "Nonprofit")
    org_mission = org.get("mission", "Mission statement not provided.")
    org_focus = org.get("focus", "Community Development")
    org_budget = org.get("budget", "1,000,000")
    org_location = org.get("location", "United States")
    org_founded = org.get("founded", "2010")
    org_programs = org.get("programs", "No program details provided.")

    grant_name = grant.get("name", "Target Grant")
    grant_funder = grant.get("funder", "Funding Organization")
    grant_amount = grant.get("amount", "$100,000")

    current_year = date.today().year
    try:
        years_served = max(1, current_year - int(org_founded))
    except (TypeError, ValueError):
        years_served = max(1, current_year - 2010)

    primary_focus = org_focus.split(",")[0].strip().lower() if org_focus else "community impact"

    return textwrap.dedent(
        f"""\
        Executive Summary

        {org_name} respectfully submits this proposal to {grant_funder} for consideration under the {grant_name}. Our organization has dedicated {years_served} years to advancing {primary_focus} outcomes across {org_location}, and this grant represents a transformative opportunity to scale our most impactful work.

        Organization Background

        Founded in {org_founded}, {org_name} is a {org_type} with an annual operating budget of ${org_budget}. {org_mission} Our programs have reached thousands of beneficiaries annually, establishing us as a trusted leader in our region.

        Project Description

        With support from {grant_funder}, we will launch a comprehensive initiative directly addressing the priorities of the {grant_name}. This project will deploy evidence-based strategies across {org_location} to create measurable, lasting change in the communities we serve. Our experienced team will leverage existing infrastructure and partnerships to maximize impact from day one of the grant period.

        Expected Outcomes

        • 40% increase in community beneficiaries directly served
        • Three replicable program models documented and shared sector-wide
        • Sustainable funding and operational model established beyond grant period
        • Quarterly data reports and final evaluation submitted to funder

        Budget Overview

        We are requesting {grant_amount} to support personnel, direct program delivery, evaluation, and administration over a 12-month period. All funds will be managed in accordance with federal guidelines, and a detailed budget with full narrative is attached. {org_name} has a demonstrated record of strong fiscal stewardship across all prior grant relationships.

        Program Notes

        {org_programs}
        """
    ).strip()


app = Flask(__name__)


@app.get("/")
def index():
    profile = sample_profile()
    grants = sample_grants()
    return render_template("index.html", profile=profile, grants=grants)


@app.post("/run")
def run_prototype():
    profile = profile_from_form(request.form)
    grants = sample_grants()
    selected_grant_id = request.form.get("selected_grant_id", "").strip() or None
    auto_approve = request.form.get("approve_and_submit") == "on"

    agent = GrantAgentPrototype(profile=profile, grants=grants)
    result = agent.execute(selected_grant_id=selected_grant_id, auto_approve=auto_approve)
    return render_template("result.html", profile=profile, result=result)


@app.post("/api/proposal")
def api_proposal():
    payload = request.get_json(silent=True) or {}
    org = payload.get("org") or {}
    grant = payload.get("grant") or {}
    proposal = generate_proposal_text(org=org, grant=grant)
    return {"proposal": proposal}


@app.get("/health")
def health():
    return {"status": "ok", "service": "hackforge-grant-agent"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HackForge grant agent Flask prototype")
    parser.add_argument("--cli", action="store_true", help="Run terminal demo instead of Flask server")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-submit if no blockers")
    parser.add_argument("--host", default="127.0.0.1", help="Flask host")
    parser.add_argument("--port", default=5000, type=int, help="Flask port")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cli:
        run_cli(auto_approve=args.auto_approve)
        return
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
