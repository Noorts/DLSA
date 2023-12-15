import time

from starlette.middleware.base import BaseHTTPMiddleware


class TraceTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        if process_time > 0.1:
            print(f"{request.method} {request.url} {process_time:.2f}s")

        return response
