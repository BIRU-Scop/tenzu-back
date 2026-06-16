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

from django import forms
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminSplitDateTime
from django.core.exceptions import ValidationError
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.db.models import Case, CharField, IntegerField, Value, When
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from martor.widgets import AdminMartorWidget

from base.db import admin
from feeds.models import FeedItem, FeedItemStatus, FeedItemType
from ninja_jwt.utils import aware_utcnow

# Status display order in the admin list (from most upcoming to oldest). The
# sort rank derives from it (index in this tuple), so there are no magic numbers.
_STATUS_DISPLAY_ORDER = (
    FeedItemStatus.SCHEDULED,
    FeedItemStatus.ACTIVE,
    FeedItemStatus.EXPIRED,
)


def _status_annotation(at: datetime) -> Case:
    """Classify each FeedItem (scheduled/active/expired) in SQL, from the bounds
    defined on the model (`FeedItem.published_q` / `expired_q`)."""
    return Case(
        When(~FeedItem.published_q(at), then=Value(FeedItemStatus.SCHEDULED.value)),
        When(FeedItem.expired_q(at), then=Value(FeedItemStatus.EXPIRED.value)),
        default=Value(FeedItemStatus.ACTIVE.value),
        output_field=CharField(),
    )


def _status_order_annotation() -> Case:
    """Sort rank derived from `_STATUS_DISPLAY_ORDER` (assumes `status` annotated)."""
    return Case(
        *(
            When(status=member.value, then=Value(rank))
            for rank, member in enumerate(_STATUS_DISPLAY_ORDER)
        ),
        output_field=IntegerField(),
    )


class FeedItemAdminForm(forms.ModelForm):
    # The model stores a single `active_period` range; the admin edits it through
    # two date fields, reassembled into the range on save.
    publication_date = forms.SplitDateTimeField(
        label=_("publication date"), widget=AdminSplitDateTime()
    )
    expiration_date = forms.SplitDateTimeField(
        label=_("expiration date"), required=False, widget=AdminSplitDateTime()
    )

    class Meta:
        model = FeedItem
        fields = [
            "title",
            "type",
            "content",
            "action_title",
            "action_url",
        ]
        widgets = {
            "content": AdminMartorWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publication_date"].initial = self.instance.publication_date
        self.fields["expiration_date"].initial = self.instance.expiration_date

        tz_name = timezone.get_current_timezone_name()
        for name in ("publication_date", "expiration_date"):
            self.fields[name].help_text = _("Timezone: %(tz)s (stored in UTC).") % {
                "tz": tz_name
            }

    def clean(self):
        cleaned = super().clean()
        item_type = cleaned.get("type")
        action_title = cleaned.get("action_title") or ""
        action_url = cleaned.get("action_url") or ""
        publication_date = cleaned.get("publication_date")
        expiration_date = cleaned.get("expiration_date")

        if item_type == FeedItemType.CALL_TO_ACTION:
            if not action_title:
                self.add_error("action_title", _("Required for a call-to-action."))
            if not action_url:
                self.add_error("action_url", _("Required for a call-to-action."))
        if action_title and not action_url:
            self.add_error(
                "action_url",
                _("Required when an action title is set."),
            )

        if publication_date and expiration_date and expiration_date < publication_date:
            self.add_error(
                "expiration_date",
                _("The end date cannot be earlier than the publication date."),
            )

        if publication_date:
            self.instance.active_period = DateTimeTZRange(
                publication_date, expiration_date, bounds="[]"
            )

        # At most one active release (without an end date) at a time.
        if item_type == FeedItemType.RELEASE and expiration_date is None:
            others = FeedItem.objects.filter(
                type=FeedItemType.RELEASE, active_period__upper_inf=True
            )
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            existing = others.first()
            if existing is not None:
                raise ValidationError(
                    _(
                        "An active release without an end date already exists: "
                        "“%(title)s”. Close it first or set an end date."
                    )
                    % {"title": existing.title}
                )

        if item_type == FeedItemType.MAINTENANCE and publication_date:
            others = FeedItem.objects.filter(
                type=FeedItemType.MAINTENANCE,
                active_period__overlap=self.instance.active_period,
            )
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            conflict = others.first()
            if conflict is not None:
                end = (
                    f"{conflict.expiration_date:%Y-%m-%d %H:%M}"
                    if conflict.expiration_date
                    else "∞"
                )
                raise ValidationError(
                    _(
                        "This maintenance overlaps “%(title)s” "
                        "(from %(start)s to %(end)s)."
                    )
                    % {
                        "title": conflict.title,
                        "start": f"{conflict.publication_date:%Y-%m-%d %H:%M}",
                        "end": end,
                    }
                )

        return cleaned


class FeedItemStatusFilter(SimpleListFilter):
    title = _("status")
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return FeedItemStatus.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    form = FeedItemAdminForm
    list_display = (
        "title",
        "type",
        "publication_date",
        "expiration_date",
        "status",
    )
    list_filter = ("type", FeedItemStatusFilter)
    search_fields = ("title",)
    ordering = ("-active_period",)
    readonly_fields = (
        "id",
        "b64id",
        "created_at",
        "created_by",
        "modified_at",
    )
    fieldsets = (
        (None, {"fields": (("id", "b64id"), "title", "type", "content")}),
        (
            _("Action (call-to-action)"),
            {"fields": ("action_title", "action_url")},
        ),
        (_("Scheduling"), {"fields": ("publication_date", "expiration_date")}),
        (_("Metadata"), {"fields": (("created_at", "created_by"), "modified_at")}),
    )

    @admin.display(description=_("status"), ordering="status_order")
    def status(self, obj: FeedItem) -> str:
        # `status` is annotated by get_queryset → translated label via the enum.
        return FeedItemStatus(obj.status).label

    def get_queryset(self, request):
        now = aware_utcnow()
        return (
            super()
            .get_queryset(request)
            .annotate(status=_status_annotation(now))
            .annotate(status_order=_status_order_annotation())
        )

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
