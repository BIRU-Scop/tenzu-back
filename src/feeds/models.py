# Copyright (C) 2026 BIRU
#
# This file is part of Tenzu.
#
# Tenzu is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# You can contact BIRU at ask@biru.sh

from datetime import datetime

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.db.models import BaseDBModel
from base.db.models.mixins import CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin
from ninja_jwt.utils import aware_utcnow


def default_active_period() -> DateTimeTZRange:
    return DateTimeTZRange(aware_utcnow(), None, bounds="[)")


class FeedItemType(models.TextChoices):
    MAINTENANCE = "maintenance", _("Maintenance")
    RELEASE = "release", _("Release")
    CALL_TO_ACTION = "call_to_action", _("Call to action")


class FeedItemStatus(models.TextChoices):
    SCHEDULED = "scheduled", _("Scheduled")
    ACTIVE = "active", _("Active")
    EXPIRED = "expired", _("Expired")


class FeedItem(BaseDBModel, CreatedMetaInfoMixin, ModifiedAtMetaInfoMixin):
    title = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        verbose_name=_("title"),
    )
    content = models.TextField(
        null=False,
        blank=False,
        verbose_name=_("content"),
        help_text=_("Markdown content."),
    )
    type = models.CharField(
        max_length=32,
        null=False,
        blank=False,
        choices=FeedItemType.choices,
        verbose_name=_("type"),
    )
    action_title = models.CharField(
        max_length=30,
        null=False,
        blank=True,
        default="",
        verbose_name=_("action title"),
    )
    action_url = models.URLField(
        null=False,
        blank=True,
        default="",
        verbose_name=_("action url"),
    )
    active_period = DateTimeRangeField(
        null=False,
        blank=False,
        default=default_active_period,
        verbose_name=_("active period"),
    )
    read_by = models.ManyToManyField(
        "users.User",
        through="FeedItemReadStatus",
        related_name="read_feed_items",
        verbose_name=_("read by"),
    )

    class Meta:
        verbose_name = _("feed item")
        verbose_name_plural = _("feed items")
        ordering = ["-active_period"]
        constraints = [
            # At most one release without an end date (the active changelog).
            models.UniqueConstraint(
                fields=["type"],
                condition=Q(
                    type=FeedItemType.RELEASE,
                    active_period__upper_inf=True,
                ),
                name="%(app_label)s_%(class)s_unique_active_release",
            ),
            # No two maintenance items with overlapping windows.
            ExclusionConstraint(
                name="%(app_label)s_%(class)s_no_overlapping_maintenance_or_release",
                expressions=[
                    ("active_period", RangeOperators.OVERLAPS),
                    ("type", RangeOperators.EQUAL),
                ],
                condition=Q(type=FeedItemType.MAINTENANCE)
                | Q(type=FeedItemType.RELEASE),
            ),
            # A call-to-action must carry both an action title and an action url.
            models.CheckConstraint(
                condition=(
                    ~Q(type=FeedItemType.CALL_TO_ACTION)
                    | (~Q(action_title="") & ~Q(action_url=""))
                ),
                name="%(app_label)s_%(class)s_cta_requires_action_fields",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.type}] {self.title}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id} [{self.type}] {self.title}>"

    @property
    def publication_date(self) -> datetime:
        return self.active_period.lower

    @property
    def expiration_date(self) -> datetime | None:
        return self.active_period.upper

    def get_status(self, at: datetime | None = None) -> FeedItemStatus:
        at = at or aware_utcnow()
        period = self.active_period
        if at in period:
            return FeedItemStatus.ACTIVE
        if not period.lower_inf and (
            at < period.lower if period.lower_inc else at <= period.lower
        ):
            return FeedItemStatus.SCHEDULED
        return FeedItemStatus.EXPIRED

    def is_active(self, at: datetime | None = None) -> bool:
        return self.get_status(at) is FeedItemStatus.ACTIVE


class FeedItemReadStatus(BaseDBModel):
    feed_item = models.ForeignKey(
        FeedItem,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="read_statuses",
        verbose_name=_("feed item"),
    )
    user = models.ForeignKey(
        "users.User",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="feed_item_read_statuses",
        verbose_name=_("user"),
    )
    read_at = models.DateTimeField(
        null=False,
        blank=False,
        default=aware_utcnow,
        verbose_name=_("read at"),
    )

    class Meta:
        verbose_name = _("feed item read status")
        verbose_name_plural = _("feed item read statuses")
        constraints = [
            models.UniqueConstraint(
                fields=["feed_item", "user"],
                name="feeds_feeditemreadstatus_unique_user_item",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} read {self.feed_item_id} at {self.read_at}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.feed_item_id} / {self.user_id}>"
