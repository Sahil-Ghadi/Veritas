"""
ARQ Worker — run as a SEPARATE process:

    arq worker.WorkerSettings

Works with local Redis (redis://) and Upstash (rediss://) equally.
"""
import os
from arq.connections import RedisSettings
from tasks import analyze_whatsapp_task

from dotenv import load_dotenv
load_dotenv()


class WorkerSettings:
    functions = [analyze_whatsapp_task]
    # from_dsn handles passwords, SSL (rediss://), and plain redis:// URLs
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    # Maximum retries on task failure
    max_jobs = 10
