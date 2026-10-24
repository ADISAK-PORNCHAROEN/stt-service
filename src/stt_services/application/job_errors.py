class JobNotFound(LookupError):
    pass


class JobExpired(JobNotFound):
    pass


class JobQueueFull(ValueError):
    pass


class ResultUnavailable(LookupError):
    pass


class ResultMissing(JobNotFound):
    pass


class ResultBusy(ResultUnavailable):
    pass
