class JobNotFound(LookupError):
    pass


class JobExpired(JobNotFound):
    pass


class JobQueueFull(ValueError):
    pass


class InvalidModel(ValueError):
    pass


class InvalidTranscript(ValueError):
    pass


class TranscriptTooLarge(ValueError):
    pass


class ResultUnavailable(LookupError):
    pass


class ResultMissing(JobNotFound):
    pass


class ResultBusy(ResultUnavailable):
    pass
