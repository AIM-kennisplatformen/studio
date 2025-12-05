from typedb.driver import TypeDB, SessionType, TransactionType
from datetime import datetime
from typing import List, Dict, Any, Optional

class TypeDBSink:
    def __init__(self, host: str = "knowledgeplatform-typedb:1729", database: str = "knowledgeplatform") -> None:
        self.driver = TypeDB.core_driver(host)
        self.database = database

    def fetch_person_timesheets(
        self, email: str, year: Optional[int] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch all timesheet records (booked, budgeted, projected, remaining)
        for a given person identified by email.
        Optionally filter by year.
        """
        rows: List[Dict[str, Any]] = []
        with self.driver.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as tx:
                query = f"""
                match
                  $p isa person, has address-email "{email}";
                  $proj isa projectlike, has namelike-name $pn;
                  $rel (books-hours: $p, charges-hours: $proj) isa timesheet,
                       has timesheets-hours $h,
                       has billable $b,
                       has date-event-registration $d;
                get $rel, $pn, $h, $b, $d;
                limit {limit};
                """
                for ans in tx.query.get(query):
                    rel_type = ans.get("rel").as_relation().get_type().get_label().name
                    raw_date = ans.get("d").as_attribute().get_value()

                    if isinstance(raw_date, str):
                        parsed_date = datetime.fromisoformat(raw_date)
                    else:
                        parsed_date = raw_date

                    record = {
                        "relation_type": rel_type,
                        "project_name": ans.get("pn").as_attribute().get_value(),
                        "hours": float(ans.get("h").as_attribute().get_value()),
                        "billable": bool(ans.get("b").as_attribute().get_value()),
                        "date": parsed_date,
                        "year": parsed_date.year,
                    }

                    if year is None or record["year"] == year:
                        rows.append(record)

        # Sort by date within the year
        rows.sort(key=lambda r: r["date"])
        return rows
