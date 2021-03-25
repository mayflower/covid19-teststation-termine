from datetime import datetime, timedelta

import logging
import json
import hug
from access_control.access_control import super_admin_authentication
from db.directives import PeeweeSession
from db.model import TimeSlot, Appointment, FrontendConfig

log = logging.getLogger('super_admin_api')


@hug.cli()
@hug.delete("/timeslots", requires=super_admin_authentication)
def delete_timeslots(
        db: PeeweeSession,
        year: hug.types.number,
        month: hug.types.number,
        day: hug.types.number,
        start_hour: hug.types.number,
        start_min: hug.types.number,
        num_slots: hug.types.number,
        for_real: hug.types.boolean = False
):
    """
    [--year] <number> [--month] <number> [--day] <number> [--start_hour] <number> [--start_min] <number> [--num_slots] <number> [--for_real]
    deletes timeslots and their corresponsing appointments if they are not booked
    """
    with db.atomic():
        dto = datetime(year, month, day, start_hour, start_min, tzinfo=None)
        tomorrow = datetime(year, month, day, tzinfo=None) + timedelta(days=1)
        ts = TimeSlot.select().where(
            (TimeSlot.start_date_time >= dto) & (TimeSlot.start_date_time < tomorrow)).order_by(
            TimeSlot.start_date_time).limit(num_slots)
        if not for_real:
            log.info(
                f"I would delete the following time slots {ts.count()} - run with --for_real if these are correct")
            raise hug.HTTP_NOT_MODIFIED
        else:
            log.info(f"Deleting the following time slots")
        tsids_to_delete = []
        for t in ts:
            tsids_to_delete.append(t.id)
            log.info(f"ID: {t.id} - {t.start_date_time}")
        if not tsids_to_delete:
            log.error("No matching timeslots found! Exiting.")
            raise hug.HTTPBadRequest
        apts = Appointment.select().where(Appointment.time_slot.in_(tsids_to_delete))
        log.info(
            f"this {'will' if for_real else 'would'} affect the following appointments")
        apts_to_delete = []
        for apt in apts:
            apts_to_delete.append(apt)
            log.info(
                f"ID: {apt.id} - {apt.time_slot.start_date_time}: {'booked!' if apt.booked else 'free'}")
        if all(not apt.booked for apt in apts_to_delete):
            log.info(
                f"none of these appointments are booked, so I {'will' if for_real else 'would'} delete them")
            if for_real:
                aq = Appointment.delete().where(
                    Appointment.id.in_([a.id for a in apts_to_delete]))
                tq = TimeSlot.delete().where(TimeSlot.id.in_(tsids_to_delete))
                aq.execute()
                tq.execute()
                log.info("Done!")
        else:
            log.error(
                f"Some of these appointments are already booked, {'will' if for_real else 'would'} not delete!")


@hug.cli()
@hug.put("/frontend_config", requires=super_admin_authentication)
def set_frontend_config(db: PeeweeSession, instance_name: hug.types.text, long_instance_name: hug.types.text,
                        contact_info_bookings: hug.types.text, contact_info_appointments: hug.types.text = None,
                        form_fields: hug.types.text = "base,address,dayOfBirth,reason",
                        for_real: hug.types.smart_boolean = False):
    """
    [--instance_name] <string> [--long_instance_name] <string> [--contact_info_bookings] <string> [--contact_info_appointments <string=None>] [--form_fields <string="base,address,dayOfBirth,reason">] [--for_real]
    """
    with db.atomic():

        if not contact_info_appointments:
            appointments_contact = contact_info_bookings
        else:
            appointments_contact = contact_info_appointments

        template = {
            "instanceName": f"{instance_name}",
            "longInstanceName": f"{long_instance_name}",
            "contactInfoCoupons": f"{contact_info_bookings}",
            "contactInfoAppointment": f"{appointments_contact}",
            "formFields": form_fields.split(","),
        }

        if not for_real:
            log.info(f"This would update the config with '{json.dumps(template, indent=2)}'. "
                     f"Run with --for_real if you are sure.")
            raise hug.HTTP_NOT_MODIFIED
        else:
            log.info(
                f"Updating the config with '{json.dumps(template, indent=2)}'.")
            try:
                config = FrontendConfig.get()
                config.config = template
            except FrontendConfig.DoesNotExist:
                config = FrontendConfig.create(config=template)

            config.save()
            log.info("Done.")
