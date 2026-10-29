"""Internal CPU-only API. One process; invoke from the application backend."""
import asyncio
import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pipeline import Reviewer
from jd_parser import JDPreparationError, prepare_jd


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)
    weight: int = Field(ge=1, le=5)


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sample_id: str = Field(default="new-cv", min_length=1, max_length=100)
    cv_text: str = Field(min_length=1, max_length=30000)
    requirements: list[Requirement] | None = Field(default=None, min_length=1, max_length=20)
    jd_text: str | None = Field(default=None, min_length=1, max_length=20000)
    job_title: str | None = Field(default=None, max_length=200)
    job_profile: dict | None = None

    @model_validator(mode="after")
    def one_source(self):
        if sum(value is not None for value in (self.requirements, self.jd_text, self.job_profile)) != 1:
            raise ValueError("Truyền đúng một trong jd_text, job_profile hoặc requirements")
        if self.job_title is not None and self.jd_text is None:
            raise ValueError("job_title chỉ dùng cùng jd_text")
        return self


class JDRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    jd_text: str = Field(min_length=1, max_length=20000)
    job_title: str = Field(default="", max_length=200)


@asynccontextmanager
async def lifespan(app):
    key = os.environ.get("INTERNAL_API_KEY", "")
    if len(key) < 32:
        raise RuntimeError("Đặt INTERNAL_API_KEY ngẫu nhiên, ít nhất 32 ký tự")
    app.state.key = key
    app.state.reviewer = Reviewer(os.environ["CVAI_ARTIFACT_DIR"], threads=int(os.environ.get("CVAI_THREADS", "2")))
    app.state.busy = False
    yield


app = FastAPI(title="FutureCV lightweight internal evaluator", lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/health")
async def health():
    return {"status": "ok"}


def authenticate(key):
    if not hmac.compare_digest(key.encode(), app.state.key.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/jobs/prepare")
async def prepare_job(body: JDRequest, x_internal_api_key: str = Header(default="")):
    authenticate(x_internal_api_key)
    try:
        return prepare_jd(body.jd_text, body.job_title)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/review")
async def review(body: Request, x_internal_api_key: str = Header(default="")):
    authenticate(x_internal_api_key)
    if app.state.busy:
        raise HTTPException(status_code=429, detail="Đang xử lý CV khác; hãy thử lại sau")
    app.state.busy = True
    try:
        task = asyncio.create_task(asyncio.to_thread(app.state.reviewer.review, body.model_dump(exclude_none=True)))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # A disconnected caller must not free the slot while CPU work continues.
            await task
            raise
    except JDPreparationError as error:
        raise HTTPException(status_code=422, detail={"message": str(error), "jd_profile": error.profile}) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        app.state.busy = False
