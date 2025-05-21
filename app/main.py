from app.api import service_call, user, course, quiz, llm, sse
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
    (service_call.router, ["Системные вызовы"]),
    (user.router, ["Управление пользователем"]),
    (course.router, ['Управление курсами']),
    (quiz.router, ['Управление']),
    (llm.router, ['Взаимодействие с LLM']),
    (sse.router, ['SSE'])
]

include_routers(root_routers, "")
