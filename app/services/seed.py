from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import get_pin_hash, normalize_phone
from app.db.session import SessionLocal
from app.models import Customer, Role, User
from app.models.user import UserStatus

REFERENCE_ROLES: tuple[dict[str, str], ...] = (
    {
        "name": "super_admin",
        "description": "Full administrative access.",
    },
    {
        "name": "operations_manager",
        "description": "Operations coordination access.",
    },
    {
        "name": "dispatcher",
        "description": "Dispatch and trip monitoring access.",
    },
    {
        "name": "finance",
        "description": "Expense and finance access.",
    },
    {
        "name": "customer",
        "description": "Customer portal access.",
    },
)


def run_startup_seeds() -> None:
    with SessionLocal() as session:
        _seed_roles(session)
        _seed_admin_user(session)


def _seed_roles(session) -> None:
    existing_roles = {role.name for role in session.scalars(select(Role)).all()}

    for role_data in REFERENCE_ROLES:
        if role_data["name"] in existing_roles:
            continue
        session.add(Role(**role_data))

    session.commit()


def _seed_admin_user(session) -> None:
    settings = get_settings()
    normalized_phone = normalize_phone(settings.admin_seed_phone)
    existing_user = session.scalar(select(User).where(User.phone == normalized_phone))
    if existing_user is not None:
        return

    role = session.scalar(select(Role).where(Role.name == settings.admin_seed_role))
    if role is None:
        raise RuntimeError(
            f"Role '{settings.admin_seed_role}' was not found during admin seed."
        )

    session.add(
        User(
            phone=normalized_phone,
            full_name=settings.admin_seed_full_name,
            pin_hash=get_pin_hash(settings.admin_seed_pin.get_secret_value()),
            role_id=role.id,
            status=UserStatus.ACTIVE,
        )
    )
    session.commit()
