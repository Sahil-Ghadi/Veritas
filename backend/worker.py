"""
ARQ Worker — run as a separate process.
"""
import os
from arq.connections import RedisSettings
from tasks import analyze_whatsapp_task

from dotenv import load_dotenv
load_dotenv()

import redis.exceptions

class WorkerSettings:
    functions = [analyze_whatsapp_task]
    
    # from_dsn handles passwords, SSL (rediss://), and plain redis:// URLs
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    redis_settings.retry_on_timeout = True
    redis_settings.retry_on_error = [redis.exceptions.ConnectionError, redis.exceptions.TimeoutError, OSError]
    
    # Maximum retries on task failure
    max_jobs = 10
    
    # Increase job timeout just in case vision inference takes a while
    job_timeout = 600
