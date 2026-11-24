from typing import TYPE_CHECKING

from django.db import models
from django_fsm import FSMField, FSMModelMixin, transition
from django_fsm_log.decorators import fsm_log_by, fsm_log_description

from assessing.models import AssessingUnit, Assessor

if TYPE_CHECKING:
    from authentication.models import User


class Application(FSMModelMixin, models.Model):
    """A land division (split, combination or boundary line adjustment) sent to the county.

    `status` can only change through the transition methods below, never by assignment, so an
    application cannot jump to a state the flow does not allow. The methods change the state
    and nothing else. Rules that need other data (checklist, tracking number, estimate, notes,
    holds) belong in a service that calls them.

    Every transition takes an optional `by` (the user who made the move) for the status log.
    `reject` and `hold` also take an optional `description` (shown in the log).
    """

    class Type(models.TextChoices):
        SPLIT = "split", "Split"
        COMBINATION = "combination", "Combination"
        BOUNDARY_LINE_ADJUSTMENT = "boundary_line_adjustment", "Boundary line adjustment"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        IN_REVIEW = "in_review", "In review"
        ON_HOLD = "on_hold", "On hold"
        REJECTED = "rejected", "Rejected"
        COMPLETE = "complete", "Complete"
        WITHDRAWN = "withdrawn", "Withdrawn"

    type = models.CharField(max_length=30, choices=Type.choices)
    assessing_unit = models.ForeignKey(
        AssessingUnit, on_delete=models.PROTECT, related_name="applications"
    )
    submitted_by = models.ForeignKey(
        Assessor, on_delete=models.PROTECT, related_name="submitted_applications"
    )
    contact = models.ForeignKey(
        Assessor, on_delete=models.PROTECT, related_name="contact_applications"
    )
    status = FSMField(default=Status.DRAFT, choices=Status.choices, protected=True)
    tracking_number = models.CharField(max_length=30, null=True, blank=True, unique=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """The tracking number, or "<Status> <type> #<id>" (e.g. "Draft split #7") before one is issued."""
        label = f"{self.get_status_display()} {self.get_type_display().lower()} #{self.pk}"
        return self.tracking_number or label

    @fsm_log_by
    @transition(field=status, source=[Status.DRAFT, Status.REJECTED], target=Status.SUBMITTED)
    def submit(self, by: User | None = None) -> None:
        """Sends the application to the county. Also used to resubmit after a rejection.

        Takes: by (User | None): who made the move, for the status log.
        Returns: None.
        """

    @fsm_log_by
    @transition(field=status, source=Status.SUBMITTED, target=Status.IN_REVIEW)
    def start_review(self, by: User | None = None) -> None:
        """County staff pick the application up.

        Takes: by (User | None): who made the move, for the status log.
        Returns: None.
        """

    @fsm_log_by
    @fsm_log_description
    @transition(field=status, source=[Status.IN_REVIEW, Status.ON_HOLD], target=Status.REJECTED)
    def reject(self, by: User | None = None, description: str | None = None) -> None:
        """Sends it back to the assessor to fix and resubmit. The reason is a note.

        Takes: by (User | None): who made the move, for the status log.
               description (str | None): shown in the log.
        Returns: None.
        """

    @fsm_log_by
    @fsm_log_description
    @transition(field=status, source=Status.IN_REVIEW, target=Status.ON_HOLD)
    def hold(self, by: User | None = None, description: str | None = None) -> None:
        """Pauses it while something outside the portal is sorted out. See `ApplicationHold`.

        Takes: by (User | None): who made the move, for the status log.
               description (str | None): shown in the log.
        Returns: None.
        """

    @fsm_log_by
    @transition(field=status, source=Status.ON_HOLD, target=Status.IN_REVIEW)
    def resume(self, by: User | None = None) -> None:
        """Takes it off hold and puts it back in review.

        Takes: by (User | None): who made the move, for the status log.
        Returns: None.
        """

    @fsm_log_by
    @transition(field=status, source=Status.IN_REVIEW, target=Status.COMPLETE)
    def complete(self, by: User | None = None) -> None:
        """County staff finish processing it.

        Takes: by (User | None): who made the move, for the status log.
        Returns: None.
        """

    @fsm_log_by
    @transition(
        field=status,
        source=[Status.DRAFT, Status.SUBMITTED, Status.IN_REVIEW, Status.ON_HOLD, Status.REJECTED],
        target=Status.WITHDRAWN,
    )
    def withdraw(self, by: User | None = None) -> None:
        """The assessor pulls it back before it is complete.

        Takes: by (User | None): who made the move, for the status log.
        Returns: None.
        """
