import logger
from fastapi import HTTPException

from config.core import DbSession

from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment

from v1.marker_result.model import MarkerResult

async def get_last_submission(
        member: StudentMember,
        enrollment: CurrentEnrollment,
        db: DbSession = None # type: ignore
    ):

    last_submission = db.query(MarkerResult).filter(
            MarkerResult.enrollment_id == enrollment.id
        ).first()

    return last_submission