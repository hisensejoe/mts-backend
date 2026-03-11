from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    booking_requests,
    customer_portal,
    customers,
    dashboard,
    drivers,
    expenses,
    health,
    routes,
    trips,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(booking_requests.router)
api_router.include_router(booking_requests.customer_router)
api_router.include_router(customer_portal.router)
api_router.include_router(customers.router)
api_router.include_router(dashboard.router)
api_router.include_router(drivers.router)
api_router.include_router(expenses.router)
api_router.include_router(routes.router)
api_router.include_router(trips.router)
api_router.include_router(vehicles.router)
