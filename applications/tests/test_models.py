from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from django_fsm import TransitionNotAllowed
from django_fsm_log.models import StateLog
from parameterized import parameterized

from applications.models import Application, ApplicationHold
from applications.tests.factories import ApplicationFactory, ApplicationHoldFactory
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


class ApplicationHoldTests(TestCase):
    open_hold: ApplicationHold
    released_hold: ApplicationHold

    @classmethod
    def setUpTestData(cls) -> None:
        cls.open_hold = ApplicationHoldFactory.create()
        cls.released_hold = ApplicationHoldFactory.create(released=True)

    def test_new_hold_is_open(self) -> None:
        self.assertTrue(self.open_hold.is_open)
        self.assertIsNone(self.open_hold.released_at)
        self.assertIsNone(self.open_hold.released_by)

    def test_released_hold_is_not_open(self) -> None:
        self.assertFalse(self.released_hold.is_open)

    def test_str(self) -> None:
        self.assertEqual(
            str(self.open_hold), f"Delinquent taxes hold on {self.open_hold.application}"
        )

    def test_application_keeps_every_hold(self) -> None:
        application = self.open_hold.application
        second = ApplicationHoldFactory.create(
            application=application,
            kind=ApplicationHold.Kind.DEED_NOT_RECORDED,
            placed_at=self.open_hold.placed_at + timedelta(days=1),
        )

        self.assertEqual(list(application.holds.all()), [second, self.open_hold])

    def test_application_cannot_be_deleted_while_it_has_holds(self) -> None:
        with self.assertRaises(ProtectedError):
            self.open_hold.application.delete()

    @parameterized.expand([("placed_by", "placed_by"), ("released_by", "released_by")])
    def test_users_cannot_be_deleted_while_a_hold_names_them(self, _name: str, field: str) -> None:
        with self.assertRaises(ProtectedError):
            getattr(self.released_hold, field).delete()

    def test_open_returns_only_unreleased_holds(self) -> None:
        self.assertEqual(list(ApplicationHold.objects.open()), [self.open_hold])

    def test_open_works_through_the_application(self) -> None:
        application = self.open_hold.application
        ApplicationHoldFactory.create(application=application, released=True)

        self.assertEqual(list(application.holds.open()), [self.open_hold])

    def test_open_is_empty_when_every_hold_on_the_application_is_released(self) -> None:
        application = self.released_hold.application
        ApplicationHoldFactory.create(application=application, released=True)

        self.assertFalse(application.holds.open().exists())

    def test_second_open_hold_of_the_same_kind_is_rejected(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            ApplicationHoldFactory.create(application=self.open_hold.application)

    def test_open_holds_of_different_kinds_can_coexist(self) -> None:
        ApplicationHoldFactory.create(
            application=self.open_hold.application, kind=ApplicationHold.Kind.OTHER
        )

        self.assertEqual(self.open_hold.application.holds.open().count(), 2)

    def test_new_hold_of_a_kind_is_allowed_after_the_last_one_is_released(self) -> None:
        application = self.released_hold.application

        ApplicationHoldFactory.create(application=application)

        self.assertEqual(application.holds.count(), 2)

    def test_hold_can_be_released_without_naming_a_user(self) -> None:
        hold = ApplicationHoldFactory.create(
            released_at=timezone.now() + timedelta(hours=1), released_by=None
        )

        self.assertFalse(hold.is_open)
