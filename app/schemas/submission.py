from pydantic import BaseModel, Field


class TestCase(BaseModel):
    __test__ = False
    stdin: str = ""
    expected_output: str = ""


class SubmissionRequest(BaseModel):
    language: str = Field(default="python")
    source_code: str = Field(min_length=1)
    test_cases: list[TestCase] = Field(min_length=1, max_length=20)
    time_limit: float = Field(default=2.0, gt=0, le=10)
    memory_limit: int = Field(default=128000, gt=0, le=512000)


class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str