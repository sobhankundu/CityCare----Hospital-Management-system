from database.models import Doctor


def all_doctors(session, department: str = None, active_only: bool = True):
    q = session.query(Doctor)
    if active_only:
        q = q.filter_by(is_active=True)
    if department:
        q = q.filter_by(department=department)
    return q.order_by(Doctor.department, Doctor.name).all()


def doctors_by_department(session):
    """Returns {department: [Doctor, ...]} for directory / booking pages."""
    doctors = all_doctors(session)
    grouped = {}
    for d in doctors:
        grouped.setdefault(d.department, []).append(d)
    return grouped


def get_doctor(session, doctor_id: int):
    return session.query(Doctor).filter_by(id=doctor_id).first()
