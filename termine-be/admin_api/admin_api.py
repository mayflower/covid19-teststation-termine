import hug
from peewee import DoesNotExist, IntegrityError
from datetime import date, datetime, timedelta

from access_control.access_control import admin_authentication, UserRoles
from db.directives import PeeweeSession
from db.model import User, Booking, TimeSlot, Appointment
from config import config
from secret_token.secret_token import get_random_string, hash_pw
from cli import get_free_timeslots_between


@hug.get("/user", requires=admin_authentication)
def get_users():
    """
    SELECT u.user_name, u.coupons, COUNT(b.id)
    FROM "user" u
    JOIN booking b ON b.booked_by = u.user_name
    GROUP BY u.user_name, u.coupons
    """
    users = User.select().where(User.role != UserRoles.ANON).order_by(
        User.role.desc(), User.user_name)
    return [{
        "user_name": user.user_name,
        "is_admin": user.role == UserRoles.ADMIN,
        "total_bookings": len(Booking.select().where(
            user.user_name == Booking.booked_by)),
        "coupons": user.coupons
    } for user in users]


@hug.patch("/user", requires=admin_authentication)
def patch_user(db: PeeweeSession, user: hug.directives.user, user_name: hug.types.text, coupons: hug.types.number, is_admin: hug.types.smart_boolean):
    with db.atomic():
        try:
            edited_user = User.get(User.user_name == user_name)
            if coupons < 0:
                coupons = 0
            edited_user.coupons = coupons
            if user != edited_user:
                edited_user.role = UserRoles.ADMIN if is_admin else UserRoles.USER
            edited_user.save()
            return {
                "user_name": edited_user.user_name,
                "coupons": edited_user.coupons
            }
        except DoesNotExist as e:
            raise hug.HTTPBadRequest
        except ValueError as e:
            raise hug.HTTPBadRequest
        except AssertionError as e:
            raise hug.HTTPBadRequest


@hug.put("/user", requires=admin_authentication)
def put_user(db: PeeweeSession, newUserName: hug.types.text, newUserPassword: hug.types.text,
             newUserPasswordConfirm: hug.types.text):
    if newUserPassword != newUserPasswordConfirm:
        raise hug.HTTPBadRequest
    with db.atomic():
        try:
            name = newUserName.lower()
            salt = get_random_string(2)
            secret_password = newUserPassword
            hashed_password = hash_pw(name, salt, secret_password)
            user = User.create(user_name=name, role=UserRoles.USER,
                               salt=salt, password=hashed_password, coupons=10)
            user.save()
            return {
                "username": user.user_name
            }
        except IntegrityError:
            raise hug.HTTPConflict('User already exists.')


@hug.cli()
@hug.patch("/coupon", requires=admin_authentication)
def inc_coupon_count(db: PeeweeSession, user_name: hug.types.text, increment: hug.types.number):
    """
    [--user_name] <string> [--increment] <number>; increment the user coupon_count, to decrement give a negative number
    """
    with db.atomic():
        user = User.get(User.user_name == user_name)
        user.coupons += increment
        user.save()


@hug.cli(output=hug.output_format.pretty_json)
@hug.get("/free_slots_at", requires=admin_authentication)
def free_slots_at(db: PeeweeSession, at_datetime: hug.types.text = None, max_days_after: hug.types.number = 2):
    """
    [--at_datetime <ISO datetime string=None>] [--max_days_after <number=2>] returns a list of free slots after given date, up to date + max_days_after
    """
    start = datetime.now(tz=config.Settings.tz).replace(tzinfo=None)
    if at_datetime is not None:
        start = datetime.fromisoformat(at_datetime).replace(tzinfo=None)
    end = start + timedelta(days=max_days_after)
    return get_free_timeslots_between(db, start, end)


@hug.cli()
@hug.put("/appointments", requires=admin_authentication)
def create_appointments(
        db: PeeweeSession,
        day: hug.types.number,
        month: hug.types.number,
        year: hug.types.number = date.today().year,
        start_hour: hug.types.number = 8,
        start_min: hug.types.number = 30,
        num_slots: hug.types.number = 13,
        num_appointment_per_slot: hug.types.number = 8,
        slot_duration_min: hug.types.number = 30
):
    """
    [--day] <number> [--month] <number> [--year <number=date.today().year>] [--start_hour <number=8>] [--start_min <number=30>] [--num_slots <number=13>] [--num_appointment_per_slot <number=8>] [--slot_duration_min <number=30>]
    creates timeslots and their corresponsing appointments
    """
    with db.atomic():
        for i in range(num_slots):
            ts = TimeSlot.create(
                start_date_time=datetime(year, month, day, start_hour, start_min, tzinfo=None) + timedelta(
                    minutes=i * slot_duration_min),
                length_min=slot_duration_min)
            for _ in range(num_appointment_per_slot):
                Appointment.create(booked=False, time_slot=ts)
            ts.save()
