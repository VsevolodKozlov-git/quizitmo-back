from app.api import service_call, users
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

application = FastAPI()


origins = [
    "*"
]

application.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def include_routers(routers: list, prefix: str) -> None:
    for router_info in routers:
        router, tags = router_info
        application.include_router(router, prefix=prefix, tags=tags)

root_routers = [
    (service_call.router, ["Service Calls"]),
    (users.router, ["User Management"]),
]

include_routers(root_routers, "")
