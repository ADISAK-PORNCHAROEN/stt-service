from stt_services.domain.job_entity import JobStatus

DAY = 86_400


def terminal_retention(status: JobStatus) -> int:
    return 7 * DAY if status == JobStatus.SUCCEEDED else DAY
