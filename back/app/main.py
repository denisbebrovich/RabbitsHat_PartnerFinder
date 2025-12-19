from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.auth.router import router as router_auth
from app.api.companies.router import router as router_companies
from app.api.vacancies.router import router as router_vacancies
from app.api.hh_ru.router import router as router_hh_ru
from app.front.router import router as root_router
from app.api.emails.router import router as router_email


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    """Управление жизненным циклом приложения."""
    logger.info("Инициализация приложения...")
    yield
    logger.info("Завершение работы приложения...")


def create_app() -> FastAPI:
    """
   Создание и конфигурация FastAPI приложения.

   Returns:
       Сконфигурированное приложение FastAPI
   """
    app = FastAPI(
        version="1.0.0",
        lifespan=lifespan,
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Монтирование статических файлов
    app.mount(
        '/static',
        StaticFiles(directory='app/static'),
        name='static'
    )

    # Регистрация роутеров
    register_routers(app)

    return app


def register_routers(app: FastAPI) -> None:
    """Регистрация роутеров приложения."""
    # Корневой роутер
    # root_router = APIRouter()

    # @root_router.get("/", tags=["root"])
    # def home_page():
    #     return {
    #         "message": "Добро пожаловать! Проект создан для сообщества 'Легкий путь в Python'.",
    #         "community": "https://t.me/PythonPathMaster",
    #         "author": "Яковенко Алексей"
    #     }

    # Подключение роутеров
    app.include_router(root_router, tags=["root"])
    app.include_router(router_auth, prefix='/api/v1/auth', tags=['Auth'])
    app.include_router(router_companies, prefix='/api/v1/companies', tags=['Companies'])
    app.include_router(router_vacancies, prefix='/api/v1/vacancies', tags=['Vacancies'])
    app.include_router(router_hh_ru, prefix='/api/v1/hh-ru', tags=['hh.ru'])
    app.include_router(router_email, prefix='/api/v1/emails', tags=['Emails'])


# Создание экземпляра приложения
app = create_app()
