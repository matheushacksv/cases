from ninja import NinjaAPI

from api.endpoints.cases import router as cases_router

api = NinjaAPI()

api.add_router('', cases_router)