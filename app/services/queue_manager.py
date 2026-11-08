
import asyncio
import uuid

from app.services.judge_service import judge_submission
from app.services.job_storage import (
    initialize_database,
    create_job,
    update_job,
    get_job
)
from app.schemas.submission import SubmissionRequest


QUEUE_SIZE = 100
WORKER_COUNT = 2


class QueueManager:

    def __init__(self):
        self.queue = asyncio.Queue(maxsize=QUEUE_SIZE)
        self.workers = []

    async def submit(self, data: SubmissionRequest):

        job_id = f"job_{uuid.uuid4().hex[:12]}"

        print(f"[SUBMIT] Received job: {job_id}")

        if self.queue.full():
            print("[SUBMIT] Queue is full!")
            return None

        create_job(job_id)

        try:
            self.queue.put_nowait({
                "job_id": job_id,
                "data": data
            })

            print(f"[SUBMIT] Job added to queue: {job_id}")
            print(f"[SUBMIT] Queue size: {self.queue.qsize()}")

        except asyncio.QueueFull:
            update_job(job_id, "Failed", {
                "status": "Internal Error",
                "message": "Queue is full."
            })
            return None

        return {
            "job_id": job_id,
            "job_status": "Queued"
        }
    async def get_job(self, job_id):
        return get_job(job_id)

    async def worker(self):
        print("[WORKER] Worker started")

        while True:
            task = await self.queue.get()

            job_id = task["job_id"]
            data = task["data"]

            print(f"[WORKER] RECEIVED JOB: {job_id}")

            try:
                print("[WORKER] Updating status to Running")

                update_job(job_id, "Running")

                print("[WORKER] Status updated successfully")
                print("[WORKER] Calling judge_submission")

                result = await asyncio.to_thread(
                    judge_submission,
                    memory_limit=data.memory_limit,
                    language=data.language,
                    source_code=data.source_code,
                    test_cases=data.test_cases,
                    time_limit=data.time_limit
                )

                print("[WORKER] Judge execution completed")
                print("[WORKER] Saving result")

                update_job(job_id, "Completed", result)

                print("[WORKER] Job completed successfully")

            except Exception as error:
                print(f"[WORKER] EXCEPTION: {repr(error)}")

                try:
                    update_job(
                        job_id,
                        "Failed",
                        {
                            "status": "Internal Error",
                            "message": str(error)
                        }
                    )
                except Exception as storage_error:
                    print(f"[WORKER] STORAGE ERROR: {repr(storage_error)}")

            finally:
                self.queue.task_done()
    async def start(self):

        initialize_database()

        self.workers = [
            asyncio.create_task(self.worker())
            for _ in range(WORKER_COUNT)
        ]

        print(f"[QUEUE] Started {WORKER_COUNT} workers")

    async def stop(self):

        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(
            *self.workers,
            return_exceptions=True
        )

        print("[QUEUE] Workers stopped")


queue_manager = QueueManager()
