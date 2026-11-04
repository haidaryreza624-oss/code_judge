import asyncio
import uuid

from app.services.judge_service import judge_submission
from app.schemas.submission import SubmissionRequest


QUEUE_SIZE = 100
WORKER_COUNT = 2


class QueueManager:

    def __init__(self):
        self.queue = asyncio.Queue(maxsize=QUEUE_SIZE)
        self.jobs = {}
        self.workers = []

    async def submit(self, data: SubmissionRequest):

        job_id = f"job_{uuid.uuid4().hex[:12]}"

        job = {
            "job_id": job_id,
            "job_status": "Queued",
            "result": None
        }

        self.jobs[job_id] = job

        try:
            self.queue.put_nowait({
                "job_id": job_id,
                "data": data
            })

        except asyncio.QueueFull:
            del self.jobs[job_id]
            return None

        return {
            "job_id": job_id,
            "job_status": "Queued"
        }

    async def get_job(self, job_id):

        print("REQUESTED JOB:", job_id)
        print("AVAILABLE JOBS:", self.jobs)

        return self.jobs.get(job_id)

    async def worker(self):

        while True:

            task = await self.queue.get()

            job_id = task["job_id"]
            data = task["data"]

            self.jobs[job_id]["job_status"] = "Running"

            try:

                result = await asyncio.to_thread(
                    judge_submission,
                    memory_limit=data.memory_limit,
                    language=data.language,
                    source_code=data.source_code,
                    test_cases=data.test_cases,
                    time_limit=data.time_limit
                )

                self.jobs[job_id]["job_status"] = "Completed"
                self.jobs[job_id]["result"] = result

            except Exception as error:

                self.jobs[job_id]["job_status"] = "Failed"
                self.jobs[job_id]["result"] = {
                    "status": "Internal Error",
                    "message": str(error)
                }

            finally:
                self.queue.task_done()

    async def start(self):

        self.workers = [
            asyncio.create_task(self.worker())
            for _ in range(WORKER_COUNT)
        ]

    async def stop(self):

        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(
            *self.workers,
            return_exceptions=True
        )


queue_manager = QueueManager()