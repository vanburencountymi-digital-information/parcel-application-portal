from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import SimpleTestCase, TestCase
from django_fsm import TransitionNotAllowed
from django_fsm_log.models import StateLog
from parameterized import parameterized

from applications.models import Application
from applications.tests.factories import ApplicationFactory
from assessing.tests.factories import AssessorFactory

Status = Application.Status


class ApplicationStrTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("tracking_number", {"tracking_number": "LD-2026-00042"}, "LD-2026-00042"),
            ("draft", {}, "Draft split #None"),
            ("withdrawn", {"status": Status.WITHDRAWN}, "Withdrawn split #None"),
            (
                "other_type",
                {"type": Application.Type.COMBINATION},
                "Draft combination #None",
            ),
        ]
    )
    def test_str(self, _name: str, fields: dict[str, str], expected: str) -> None:
        self.assertEqual(str(ApplicationFactory.build(**fields)), expected)


class ApplicationConstraintTests(TestCase):
    def test_many_applications_can_have_no_tracking_number(self) -> None:
        ApplicationFactory.create_batch(2)

        self.assertEqual(Application.objects.filter(tracking_number__isnull=True).count(), 2)

    def test_duplicate_tracking_number_is_rejected(self) -> None:
        ApplicationFactory.create(tracking_number="LD-2026-00001")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ApplicationFactory.create(tracking_number="LD-2026-00001")

    def test_new_application_defaults_to_draft_with_submitter_as_contact(self) -> None:
        application = ApplicationFactory.create()

        self.assertEqual(application.status, Status.DRAFT)
        self.assertEqual(application.contact, application.submitted_by)

    @parameterized.expand([("assessing_unit",), ("submitted_by",), ("contact",)])
    def test_related_rows_cannot_be_deleted_while_an_application_uses_them(
        self, field: str
    ) -> None:
        application = ApplicationFactory.create()

        with self.assertRaises(ProtectedError):
            getattr(application, field).delete()


class ApplicationTransitionTests(TestCase):
    @parameterized.expand(
        [
            ("submit_draft", Status.DRAFT, "submit", Status.SUBMITTED),
            ("resubmit", Status.REJECTED, "submit", Status.SUBMITTED),
            ("start_review", Status.SUBMITTED, "start_review", Status.IN_REVIEW),
            ("reject", Status.IN_REVIEW, "reject", Status.REJECTED),
            ("reject_from_hold", Status.ON_HOLD, "reject", Status.REJECTED),
            ("hold", Status.IN_REVIEW, "hold", Status.ON_HOLD),
            ("resume", Status.ON_HOLD, "resume", Status.IN_REVIEW),
            ("complete", Status.IN_REVIEW, "complete", Status.COMPLETE),
            ("withdraw_draft", Status.DRAFT, "withdraw", Status.WITHDRAWN),
            ("withdraw_on_hold", Status.ON_HOLD, "withdraw", Status.WITHDRAWN),
        ]
    )
    def test_allowed_move(self, _name: str, start: str, method: str, end: str) -> None:
        application = ApplicationFactory.create(status=start)

        getattr(application, method)()
        application.save()

        application.refresh_from_db()
        self.assertEqual(application.status, end)

    @parameterized.expand(
        [
            ("complete_from_draft", Status.DRAFT, "complete"),
            ("start_review_from_draft", Status.DRAFT, "start_review"),
            ("reject_from_submitted", Status.SUBMITTED, "reject"),
            ("hold_from_submitted", Status.SUBMITTED, "hold"),
            ("resume_from_in_review", Status.IN_REVIEW, "resume"),
            ("submit_from_in_review", Status.IN_REVIEW, "submit"),
            ("reopen_complete", Status.COMPLETE, "start_review"),
            ("withdraw_complete", Status.COMPLETE, "withdraw"),
            ("withdraw_twice", Status.WITHDRAWN, "withdraw"),
        ]
    )
    def test_move_not_in_the_flow_is_refused(self, _name: str, start: str, method: str) -> None:
        application = ApplicationFactory.create(status=start)

        with self.assertRaises(TransitionNotAllowed):
            getattr(application, method)()

        self.assertEqual(application.status, start)

    def test_status_cannot_be_assigned_directly(self) -> None:
        application = ApplicationFactory.create()

        with self.assertRaises(AttributeError):
            application.status = Status.COMPLETE

    def test_each_move_is_logged_with_who_and_why(self) -> None:
        application = ApplicationFactory.create(status=Status.IN_REVIEW)
        staff = AssessorFactory.create().user

        application.reject(by=staff, description="Survey is illegible")

        entry = StateLog.objects.for_(application).get()
        self.assertEqual((entry.source_state, entry.state), (Status.IN_REVIEW, Status.REJECTED))
        self.assertEqual(entry.by, staff)
        self.assertEqual(entry.description, "Survey is illegible")
