import csv
import io
import json
import logging
import sys
from datetime import date, datetime, timedelta

import hug
from peewee import fn, DatabaseError

from api import api
from access_control.access_control import UserRoles, get_or_create_auto_user
from config import config
from db import directives
from db.migration import migrate_db, init_database
from db.model import TimeSlot, Appointment, User, Booking, Migration, FrontendConfig
from secret_token.secret_token import get_random_string, hash_pw
from admin_api import admin_api

log = logging.getLogger('cli')


@hug.default_output_format(apply_globally=False, cli=True, http=False)
def cli_output(data):
    result = io.StringIO()
    writer = csv.DictWriter(result, fieldnames=data[0].keys(), delimiter='\t')
    writer.writeheader()
    writer.writerows(data)
    return result.getvalue().encode('utf8')


def _add_one_user(db: directives.PeeweeSession, username: hug.types.text, password: hug.types.text = None,
                  role: hug.types.one_of(
                      UserRoles.user_roles()) = UserRoles.USER,
                  coupons: hug.types.number = 10):
    with db.atomic():
        name = username.lower()
        salt = get_random_string(2)
        secret_password = password or get_random_string(12)
        hashed_password = hash_pw(name, salt, secret_password)
        user = User.create(user_name=name, role=role, salt=salt,
                           password=hashed_password, coupons=coupons)
        user.save()
        return {"name": user.user_name, "password": secret_password}


@hug.cli()
def add_user(db: directives.PeeweeSession, username: hug.types.text, password: hug.types.text = None,
             role: hug.types.one_of(UserRoles.user_roles()) = UserRoles.USER,
             coupons: hug.types.number = 10):
    """
    [--username] <string> [--password] <string> [--role <one_of(UserRoles.user_roles()) = UserRoles.USER>] [--coupons <number=10>]; creates a user
    """
    return [_add_one_user(db, username, password, role, coupons)]


@hug.cli()
def get_user_roles():
    """
    get a list of available user_roles
    """
    return UserRoles.user_roles()


@hug.cli()
def add_users(db: directives.PeeweeSession, filename: hug.types.text,
              role: hug.types.one_of(UserRoles.user_roles()) = UserRoles.USER):
    """
    [--filename] <string> [--role <one_of(UserRoles.user_roles()) = UserRoles.USER>]; imports usernames from the file, one user per line, with a default of 10 coupons
    """
    with open(filename) as f:
        return [_add_one_user(db, line.strip(), role=role) for line in f]


@hug.cli()
def change_user_pw(db: directives.PeeweeSession, username: hug.types.text, password: hug.types.text, for_real: hug.types.smart_boolean = False):
    """
    [--username] <string> [--password] <string> [--for_real]; changes the passwort for given user
    """
    if not for_real:
        print(
            f"this would change {username}'s pw to {password}. Run with --for_real if you're sure.")
        sys.exit(1)
    with db.atomic():
        name = username.lower()
        salt = get_random_string(2)
        secret_password = password
        hashed_password = hash_pw(name, salt, secret_password)
        user = User.get(User.user_name == username)
        user.salt = salt
        user.password = hashed_password
        user.save()
        print(f"{user.user_name}'s pw successfully changed.")


@hug.cli()
def init_db(db: directives.PeeweeSession, for_real: hug.types.smart_boolean = False):
    """
    [--for_real]; initializes the database
    """
    if not for_real:
        print('this will create the database (potentially destroying data), run with --for_real, if you are sure '
              '*and* have a backup')
        sys.exit(1)
    else:
        with db.atomic():
            try:
                migration = Migration.get()
                print(f'Migration level is already set to version {migration.version} - implying the db has already been '
                      f'initialized. Run command `run_migrations` instead.')
                sys.exit(1)
            except DatabaseError:
                init_database()


@hug.cli()
def run_migrations(for_real: hug.types.smart_boolean = False):
    """
    [--for_real]; runs the database migrations
    """
    if not for_real:
        print('this will migrate the database (potentially destroying data), run with --for_real, if you are sure '
              '*and* have a backup')
        sys.exit(1)
    else:
        print('Start database migration...')
        migrate_db()
        print('Done.')


@hug.cli()
def get_coupon_state():
    """
    get a list of all users and their bookings and remaining coupons
    """
    ret = []
    for user in User.select():
        bookings = Booking.select().where(
            user.user_name == Booking.booked_by)
        ret.append({
            "name": user.user_name,
            "num_bookings": len(bookings),
            "coupons": user.coupons
        })
    return ret


@hug.cli()
def set_coupon_count(db: directives.PeeweeSession, user_name: hug.types.text, value: hug.types.number):
    """
    [--user_name] <string> [--value] <number>; set the user coupon_count to <value>
    """
    with db.atomic():
        user = User.get(User.user_name == user_name)
        user.coupons = value
        user.save()


@hug.cli()
def cancel_booking(db: directives.PeeweeSession, secret: hug.types.text, start_date_time: hug.types.text, for_real: hug.types.smart_boolean = False):
    """
    [--secret] <string> [--start_date_time] <ISO datetime string> [--for_real]; cancel the booking with given secret at given time
    """
    with db.atomic():
        sdt = datetime.fromisoformat(start_date_time).replace(tzinfo=None)
        timeslot = TimeSlot.get(TimeSlot.start_date_time == sdt)
        booking = Booking.select(Booking).join(Appointment).where(
            (Booking.secret == secret) &
            (Appointment.time_slot == timeslot)).get()

        if not for_real:
            print(f"This would delete the booking with id '{booking.id}' and secret '{booking.secret}'. Run with "
                  f"--for_real if you are sure.")
            sys.exit(1)
        else:
            print(
                f"Deleting the booking with id '{booking.id}' and secret '{booking.secret}'.")
            booking.appointment.booked = False
            booking.appointment.save()
            q = Booking.delete().where(Booking.id == booking.id)
            q.execute()
            print("Done.")


@hug.cli()
def load_frontend_config(db: directives.PeeweeSession, frontend_config_file: hug.types.text,
                         for_real: hug.types.smart_boolean = False):
    """
    [--frontend_config_file] <file> [--for_real] loads the config file to the database if run with --for_real
    To check the frontend_config, omit the --for_real flag
    """
    with db.atomic():
        with open(frontend_config_file, 'r') as j_file:
            try:
                new_config = json.load(j_file)
                if 'instanceName' not in new_config or 'longInstanceName' not in new_config or \
                        'contactInfoCoupons' not in new_config \
                        or 'contactInfoAppointment' not in new_config or 'formFields' not in new_config:
                    print(
                        f"Given file '{json.dumps(new_config, indent=2)}' missing required fields!")
                    sys.exit(1)
                elif type(new_config['formFields']) != list:
                    print("field formFields is not a list!")
                    sys.exit(1)
            except json.JSONDecodeError as e:
                print("The file can not decoded as json!")
                sys.exit(1)

            if not for_real:
                print(
                    f"This would update the config with '{json.dumps(new_config, indent=2)}'. "
                    f"Run with --for_real if you are sure.")
                sys.exit(1)
            else:
                print(
                    f"Updating the config with '{json.dumps(new_config, indent=2)}'.")
                try:
                    config = FrontendConfig.get()
                    config.config = new_config
                except FrontendConfig.DoesNotExist:
                    config = FrontendConfig.create(config=new_config)

                config.save()
                print("Done.")


@hug.cli(output=hug.output_format.pretty_json)
def get_bookings_created_at(db: directives.PeeweeSession, booked_at: hug.types.text):
    """
    [--booked_at <ISO datetime string>] get all bookings made at specific day or time
    Get bookings for a day with yyyy-mm-dd or one specific booking at yyyy-mm-ddThh:mm:ss.mmmmmm
    """
    with db.atomic():
        query = Booking.select(
            Booking,
            Appointment.time_slot.start_date_time.alias("start_date_time")
        ).join(Appointment).join(TimeSlot)

        booked_start = datetime.fromisoformat(booked_at).replace(tzinfo=None)

        if str(booked_start.date()) == booked_at:
            # booked_at is yyyy-mm-dd
            booked_end = booked_start.date() + timedelta(days=1)
            bookings = query.where(
                Booking.booked_at.between(booked_start, booked_end))
        else:
            # booked_at is yyyy-mm-ddThh:mm:ss.mmmmmm
            bookings = query.where(Booking.booked_at == booked_start)

        result = []
        for booking in bookings.dicts().iterator():
            del booking["appointment"]
            result.append({**booking})

        return result


def get_free_timeslots_between(db: directives.PeeweeSession, start: datetime, end: datetime):
    with db.atomic():
        now = datetime.now(tz=config.Settings.tz).replace(tzinfo=None)
        slots = TimeSlot \
            .select(TimeSlot.start_date_time, TimeSlot.length_min,
                    fn.count(Appointment.time_slot).alias("free_appointments")) \
            .join(Appointment) \
            .where(
                (TimeSlot.start_date_time >= start) & (TimeSlot.start_date_time <= end) &
                (Appointment.claim_token.is_null() | (Appointment.claimed_at +
                                                      timedelta(
                                                          minutes=config.Settings.claim_timeout_min) < now)) &
                (Appointment.booked == False)
            ) \
            .group_by(TimeSlot.start_date_time, TimeSlot.length_min) \
            .order_by(TimeSlot.start_date_time) \
            # @formatter:on
        return [{"startDateTime": str(slot.start_date_time)} for slot in slots]


@hug.cli(output=hug.output_format.pretty_json)
def free_slots_before(db: directives.PeeweeSession, at_datetime: hug.types.text = None, max_days_before: hug.types.number = 2):
    """
    [--at_datetime <ISO datetime string=None>] [--max_days_before <number=2>] returns a list of free slots before given date, up to date - max_days_before
    """
    end = datetime.now(tz=config.Settings.tz).replace(tzinfo=None)
    if at_datetime is not None:
        end = datetime.fromisoformat(at_datetime).replace(tzinfo=None)
    start = end - timedelta(days=max_days_before)
    return get_free_timeslots_between(db, start, end)


@hug.cli(output=hug.output_format.pretty_json)
def claim_appointment(db: directives.PeeweeSession, start_date_time: hug.types.text, user: hug.types.text):
    """
    [--start_date_time] START_DATE_TIME (ISO string) [--user] USER_NAME
    """
    try:
        api_claim_appointment = api.claim_appointment(
            db, start_date_time, get_or_create_auto_user(
                db, UserRoles.USER, user)
        )
    except hug.HTTPGone as e:
        return None

    return api_claim_appointment


@hug.cli(output=hug.output_format.pretty_json)
def has_booked_by(db: directives.PeeweeSession, user: hug.types.text):
    """
    USER_NAME; checks if there are bookings made by that user
    """
    return Booking.select(Booking).where(Booking.booked_by == user).count() > 0


@hug.cli(output=hug.output_format.pretty_json)
def has_booking(db: directives.PeeweeSession, booking: hug.types.json):
    """
    BOOKING_JSON; check if a booking exists for the booked person
    """
    with db.atomic():
        try:
            return Booking.select(Booking).where(
                (Booking.surname == booking["surname"])
                & (Booking.first_name == booking["first_name"])
                & (Booking.birthday == booking["birthday"])
                & (Booking.phone == booking["phone"])
                & (Booking.street == booking["street"])
                & (Booking.street_number == booking["street_number"])
                & (Booking.post_code == booking["post_code"])
                & (Booking.city == booking["city"])
            ).count() > 0
        except KeyError as e:
            print(f"Key {e} is missing in booking.")
            return None


@hug.cli(output=hug.output_format.pretty_json)
def book_followup(db: directives.PeeweeSession, booking: hug.types.json, delta_days: hug.types.number = 21, day_range: hug.types.number = 2):
    """
    BOOKING_JSON [--delta_days <number=21>][--day_range <number=2>]
    """
    if has_booked_by(db, booking["booked_by"]):
        print(
            f"User {booking['booked_by']} already booked at least one appointment.")
        return None

    start_date = datetime.fromisoformat(
        booking["start_date_time"]).replace(tzinfo=None)
    followup_date = start_date + timedelta(days=delta_days)

    slots_after = admin_api.free_slots_at(
        db, booking["booked_by"], str(followup_date), day_range)
    slots_before = free_slots_before(
        db, booking["booked_by"], str(followup_date), day_range)

    slot_count = len(slots_before) + len(slots_after)
    if slot_count == 0:
        print(
            f"No free slots available for booking: {booking} at '{followup_date}' in range of {day_range} days")
        return None

    found_time = None
    tries = -1
    claim_token = None
    while claim_token is None and tries < len(slots_after):
        tries += 1
        found_time = slots_after[tries]["startDateTime"]
        claim_token = claim_appointment(
            db, found_time, booking["booked_by"])

    tries = -1
    while claim_token is None and tries < len(slots_before):
        tries += 1
        found_time = slots_before[tries]["startDateTime"]
        claim_token = claim_appointment(
            db, found_time, booking["booked_by"])

    if claim_token is None:
        print(
            f"Failed to claim slot for booking: {booking} at '{followup_date}' in range of {day_range} days")
        return None

    booking["name"] = booking["surname"]
    booking["claim_token"] = claim_token
    booking["start_date_time"] = found_time

    print(f"Book appointment with data {booking}")
    booked = api.book_appointment(db, booking, get_or_create_auto_user(
        db, UserRoles.USER, booking["booked_by"]))

    return booked


@hug.cli()
def batch_book_followup(db: directives.PeeweeSession, delta_days: hug.types.number = 21, day_range: hug.types.number = 2):
    """
    Expects result from get_bookings_created_at piped into stdin
    delta_days: days after the first appointment
    day_range: will search appointments in that range (+ or -) of above date (nearest will be taken)
    """
    bookings = json.load(sys.stdin)

    for booking in bookings:
        booked = book_followup(db, booking, delta_days, day_range)
        if booked is not None:
            booked["time_slot"] = str(booked["time_slot"])
        print(f"Booked appointment {booked}")
