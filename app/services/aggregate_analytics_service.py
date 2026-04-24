"""AggregateAnalyticsService — scope-aware roll-up across districts, schools, or classes.

Grouping is resolved from the caller's role and filter values:
  superadmin + no filter   → group by district
  superadmin + district    → group by school
  superadmin + school      → group by class
  admin (any)              → group by class (locked to their school)
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.analytics import (
    AggregateAnalyticsResponse,
    AggregateGroupRow,
    UnitMasteryRow,
)
from app.infrastructure.database.models import Unit
from app.infrastructure.database.repositories.aggregate_repo import AggregateRepository

logger = get_logger(__name__)


def _resolve_grouping(role: str, district: str | None, school: str | None) -> str:
    if role != "superadmin":
        return "class"
    if not district:
        return "district"
    if not school:
        return "school"
    return "class"


class AggregateAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_aggregate(
        self,
        district: str | None,
        school: str | None,
        requesting_school: str | None,
        role: str,
    ) -> AggregateAnalyticsResponse:
        # School admins are always locked to their own school.
        if role != "superadmin":
            district = None
            school = requesting_school

        grouping = _resolve_grouping(role, district, school)
        repo = AggregateRepository(self._session)

        # Sequential — AsyncSession is not safe for concurrent use.
        groups_raw = await repo.get_groups(grouping, district, school)
        problems_map = await repo.get_problems_solved(grouping, district, school)
        hours_map = await repo.get_hours_active(grouping, district, school)
        weakest_raw = await repo.get_weakest_units(district, school)
        dist_map = await repo.get_mastery_distribution(district, school)

        # Fetch unit titles in one IN query.
        unit_ids = [r.unit_id for r in weakest_raw]
        title_map: dict[str, str | None] = {}
        if unit_ids:
            res = await self._session.execute(
                select(Unit.id, Unit.title).where(Unit.id.in_(unit_ids))
            )
            title_map = {row.id: row.title for row in res.all()}

        # Build group rows.
        # problems_map / hours_map are keyed by group_id (UUID str) for class-level,
        # or by group name (district/school) otherwise — match accordingly.
        def _lookup_key(row) -> str:
            return str(row.group_id) if row.group_id else (row.name or "")

        groups: list[AggregateGroupRow] = [
            AggregateGroupRow(
                name=row.name,
                group_id=row.group_id,
                student_count=int(row.student_count or 0),
                class_count=int(row.class_count or 0),
                avg_mastery=float(row.avg_mastery or 0.0),
                at_risk_count=int(row.at_risk_count or 0),
                avg_l1_score=round(float(row.avg_l1_score or 0.0), 4),
                avg_l2_score=round(float(row.avg_l2_score or 0.0), 4),
                avg_l3_score=round(float(row.avg_l3_score or 0.0), 4),
                at_risk_l2_count=int(row.at_risk_l2_count or 0),
                at_risk_l3_count=int(row.at_risk_l3_count or 0),
                high_risk_count=int(row.high_risk_count or 0),
                moderate_risk_count=int(row.moderate_risk_count or 0),
                adopted_count=int(row.adopted_count or 0),
                problems_solved=problems_map.get(_lookup_key(row), 0),
                hours_active=hours_map.get(_lookup_key(row), 0),
            )
            for row in groups_raw
            if row.name  # skip rows where group key is NULL
        ]

        # Totals — derived from group rows; no extra query.
        total_students = sum(g.student_count for g in groups)
        total_classes = sum(g.class_count for g in groups)
        total_problems = sum(g.problems_solved for g in groups)
        total_hours = sum(g.hours_active for g in groups)
        overall_at_risk = sum(g.at_risk_count for g in groups)
        overall_at_risk_l2 = sum(g.at_risk_l2_count for g in groups)
        overall_at_risk_l3 = sum(g.at_risk_l3_count for g in groups)
        overall_high_risk = sum(g.high_risk_count for g in groups)
        overall_moderate_risk = sum(g.moderate_risk_count for g in groups)
        total_adopted = sum(g.adopted_count for g in groups)
        adoption_rate = round(total_adopted / total_students, 4) if total_students else 0.0

        # Weighted average mastery (weighted by student count).
        weighted_sum = sum(g.avg_mastery * g.student_count for g in groups)
        overall_mastery = weighted_sum / total_students if total_students else 0.0

        overall_l1 = sum(g.avg_l1_score * g.student_count for g in groups) / total_students if total_students else 0.0
        overall_l2 = sum(g.avg_l2_score * g.student_count for g in groups) / total_students if total_students else 0.0
        overall_l3 = sum(g.avg_l3_score * g.student_count for g in groups) / total_students if total_students else 0.0

        weakest_units = [
            UnitMasteryRow(
                unit_id=r.unit_id,
                unit_title=title_map.get(r.unit_id),
                avg_mastery=float(r.avg_mastery or 0.0),
                student_count=int(r.student_count or 0),
            )
            for r in weakest_raw
        ]

        logger.info(
            "aggregate_analytics_computed",
            grouping=grouping,
            district=district,
            school=school,
            group_count=len(groups),
        )

        return AggregateAnalyticsResponse(
            grouping=grouping,
            groups=groups,
            total_students=total_students,
            total_classes=total_classes,
            total_problems_solved=total_problems,
            total_hours_active=total_hours,
            overall_avg_mastery=round(overall_mastery, 4),
            overall_at_risk_count=overall_at_risk,
            overall_avg_l1_score=round(overall_l1, 4),
            overall_avg_l2_score=round(overall_l2, 4),
            overall_avg_l3_score=round(overall_l3, 4),
            overall_at_risk_l2_count=overall_at_risk_l2,
            overall_at_risk_l3_count=overall_at_risk_l3,
            overall_high_risk=overall_high_risk,
            overall_moderate_risk=overall_moderate_risk,
            adoption_rate=adoption_rate,
            weakest_units=weakest_units,
            mastery_distribution=dist_map,
        )
