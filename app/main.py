from fastapi import FastAPI, HTTPException, BackgroundTasks
from app import utils
from app.schema import TransportRequest
from app.transport_job import TransportJob
import concurrent.futures

app = FastAPI()


def run_transport_job(job_data: TransportJob):
    transport_job = TransportJob(job_data)
    transport_job.run_job()


def execute_long_running_job(job_data):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(run_transport_job(job_data))


@app.post("/request-transport")
async def request_transport(job_data: TransportRequest, background_tasks: BackgroundTasks):
    try:
        utils.validate_request_data(job_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail={
                            "status": "ERROR", "error_message": str(e)})
    background_tasks.add_task(execute_long_running_job, job_data)
    return {"message": "Transportation requested"}
