from mcp.server.fastmcp import FastMCP
from studio.typedb.db_sink import TypeDBSink  # <-- your real TypeDB data-access layer
from collections import defaultdict
import datetime
from langfuse import Langfuse, observe
from typing import DefaultDict, Dict, Tuple



# -------------------------------
# Real datasink
# -------------------------------
datasink = TypeDBSink(database="knowledgeplatform")

# -------------------------------
# MCP server init
# -------------------------------
mcp = FastMCP("typedb")

langfuse = Langfuse(
  secret_key="dev-secret-key", # change in production
  public_key="dev-public-key", # change in production
  host="http://host.docker.internal:3000" # change in production
)

@mcp.tool()
@observe(name="get_weekly_summary") 
async def get_weekly_summary(email: str, year: int) -> str:
    """
    Geef een wekelijkse samenvatting van alle uren (per project en urensoort)
    voor een medewerker in een bepaald jaar.
    """
    records = datasink.fetch_person_timesheets(email, year=year, limit=10000)

    if not records:
        return f"Geen uren gevonden voor {email} in {year}."

    weekly: DefaultDict[Tuple[int, str, str], float] = defaultdict(float)

    for rec in records:
        date = rec["date"]
        if isinstance(date, str):
            date = datetime.date.fromisoformat(date)

        yr, week, _ = date.isocalendar()
        if yr != year:
            continue

        key = (week, rec["project_name"], rec["relation_type"])
        weekly[key] += rec["hours"]

    regels = [f"Wekelijkse uren voor {email} in {year}:"]
    for (week, project, relation), hours in sorted(weekly.items()):
        regels.append(f"  - Week {week} | {project} | {relation}: {hours:.2f}h")

    return "\n".join(regels)

@mcp.tool()
@observe(name="get_weekly_hours")
async def get_weekly_hours(email: str, year: int) -> str:
    """
    Geef de wekelijkse uren (budgeted, projected, remaining) per project in een bepaald jaar.
    """
    records = datasink.fetch_person_timesheets(email, year=year, limit=10000)

    # structuur: {(week, project): {"budgeted": x, "projected": y, "remaining": z}}
    per_week_project: DefaultDict[
        Tuple[int, str],
        Dict[str, float]
    ] = defaultdict(lambda: {
        "budgeted": 0.0,
        "projected": 0.0,
        "remaining": 0.0,
    })

    for rec in records:
        week = rec["week_number"]
        project = rec["project_name"]
        hours_type = rec["hours_type"]   # verwacht: "budgeted" / "projected" / "remaining"
        uren = rec["hours"]

        per_week_project[(week, project)][hours_type] += uren

    if not per_week_project:
        return f"Geen uren gevonden voor {email} in {year}."

    # Markdown tabel bouwen
    regels = [f"### Wekelijkse uren voor {email} in {year}", ""]
    regels.append("| Week | Project | Hours Budgeted | Hours Projected | Hours Remaining |")
    regels.append("|------|---------|----------------|-----------------|-----------------|")

    # sorteren op week en projectnaam
    for (week, project), data in sorted(per_week_project.items(), key=lambda x: (x[0][0], x[0][1])):
        regels.append(
            f"| {week} | {project} | "
            f"{data['budgeted']:.2f} | {data['projected']:.2f} | {data['remaining']:.2f} |"
        )

    return "\n".join(regels)



@mcp.tool()
@observe(name="get_totaal_uren")
async def get_totaal_uren(email: str) -> str:
    """
    Geef het totaal aantal (billable + niet-billable) uren voor een medewerker.
    """
    records = datasink.fetch_person_timesheets(email, limit=1000000)

    total_hours = sum(rec["hours"] for rec in records)

    if total_hours == 0.0:
        return f"Geen uren gevonden voor {email}."
    return f"Totaal aantal uren voor {email}: {total_hours:.2f} uur"
