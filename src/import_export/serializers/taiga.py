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

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import enum
import functools
from base64 import b64decode, b64encode
from datetime import datetime
from typing import Annotated, Any, Iterable, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    GetPydanticSchema,
    NonNegativeInt,
    PlainSerializer,
    conlist,
    field_validator,
)
from pydantic_core import core_schema

from base.db.models import BaseDBModel
from commons.validators import UniqueInListValidator


def db_model_to_id(v: Any) -> Any:
    if isinstance(v, BaseDBModel):
        return v.id
    return v


TenzuId = (
    UUID
    | Annotated[
        BaseDBModel,
        GetPydanticSchema(lambda _s, h: h(core_schema.is_instance_schema(BaseDBModel))),
        PlainSerializer(db_model_to_id),
    ]
)

_FileData = Annotated[
    str,
    AfterValidator(functools.partial(b64decode, validate=True)),
    PlainSerializer(b64encode),
]


class _TaigaFile(BaseModel):
    data: _FileData  # base64 encoded binary file
    name: str

    model_config = ConfigDict(extra="allow")


_TaigaCustomAttributesValue = str | int | bool

_TaigaMemberPermission = Literal[
    "view_project",
    "view_milestones",
    "add_milestone",
    "modify_milestone",
    "delete_milestone",
    "view_epics",
    "add_epic",
    "modify_epic",
    "comment_epic",
    "delete_epic",
    "view_us",
    "add_us",
    "modify_us",
    "comment_us",
    "delete_us",
    "view_tasks",
    "add_task",
    "modify_task",
    "comment_task",
    "delete_task",
    "view_issues",
    "add_issue",
    "modify_issue",
    "comment_issue",
    "delete_issue",
    "view_wiki_pages",
    "add_wiki_page",
    "modify_wiki_page",
    "comment_wiki_page",
    "delete_wiki_page",
    "view_wiki_links",
    "add_wiki_link",
    "modify_wiki_link",
    "delete_wiki_link",
]

_TaigaAnonPermission = Literal[
    "view_project",
    "view_milestones",
    "view_epics",
    "view_us",
    "view_tasks",
    "view_issues",
    "view_wiki_pages",
    "view_wiki_links",
]

_TaigaHistoryUser = (
    tuple[EmailStr | None, str] | conlist(Any, max_length=0) | None
)  # tuple (email, name) usually, [] if field was empty and None if user was not found (deleted)


class _TaigaHistoryType(enum.IntEnum):
    change = 1
    create = 2
    delete = 3


class _TaigaHistory(BaseModel):
    tenzu_id: TenzuId | None = None

    user: _TaigaHistoryUser
    created_at: datetime
    type: Literal[_TaigaHistoryType.change, _TaigaHistoryType.create]
    diff: dict
    snapshot: dict | None
    values: dict
    comment: str
    delete_comment_date: datetime | None
    delete_comment_user: _TaigaHistoryUser
    comment_versions: (
        list[dict] | None
    )  # format is {date, user: {id}, comment, comment_html} for each previous version
    edit_comment_date: datetime | None
    is_hidden: bool
    is_snapshot: bool

    model_config = ConfigDict(extra="allow")


class _TaigaAttachment(BaseModel):
    tenzu_id: TenzuId | None = None

    owner: EmailStr | None
    created_date: datetime
    modified_date: datetime
    name: str
    size: int | None
    attached_file: _TaigaFile | None
    sha1: str
    is_deprecated: bool
    description: str
    order: int

    model_config = ConfigDict(extra="allow")


class _TaigaPoints(BaseModel):
    name: str
    order: int
    value: float | None

    model_config = ConfigDict(extra="allow")


class _TaigaStatus(BaseModel):
    name: str
    slug: str
    order: int
    is_closed: bool
    color: str  # hex code

    model_config = ConfigDict(extra="allow")


class _TaigaUserStoryStatus(_TaigaStatus):
    tenzu_ids: list[TenzuId] | None = None

    is_archived: bool
    wip_limit: int | None

    model_config = ConfigDict(extra="allow")


_UniqueTaigaUserStoryStatuses = Annotated[
    list[_TaigaUserStoryStatus],
    AfterValidator(UniqueInListValidator("slug")),
    AfterValidator(UniqueInListValidator("name")),
]


class _TaigaDueDate(BaseModel):
    name: str
    order: int
    by_default: bool
    color: str  # hex code
    days_to_due: int | None

    model_config = ConfigDict(extra="allow")


class _TaigaPriority(BaseModel):
    name: str
    order: int
    color: str  # hex code

    model_config = ConfigDict(extra="allow")


class _TaigaSeverity(BaseModel):
    name: str
    order: int
    color: str  # hex code

    model_config = ConfigDict(extra="allow")


class _TaigaIssueType(BaseModel):
    name: str
    order: int
    color: str  # hex code

    model_config = ConfigDict(extra="allow")


class _TaigaSwimlaneUserStoryStatus(BaseModel):
    tenzu_id: TenzuId | None = None

    wip_limit: int | None
    status: str  # related name

    model_config = ConfigDict(extra="allow")


class _TaigaSwimlane(BaseModel):
    tenzu_id: TenzuId | None = None

    name: str
    order: int
    statuses: list[_TaigaSwimlaneUserStoryStatus] = None

    model_config = ConfigDict(extra="allow")


_UniqueTaigaSwimlanes = Annotated[
    list[_TaigaSwimlane], AfterValidator(UniqueInListValidator("name"))
]


class _TaigaRole(BaseModel):
    tenzu_id: TenzuId | None = None

    name: str
    slug: str
    order: int
    computable: bool
    permissions: list[_TaigaMemberPermission] | None = None

    model_config = ConfigDict(extra="allow")


_UniqueTaigaRoles = Annotated[
    list[_TaigaRole], AfterValidator(UniqueInListValidator("slug"))
]


class _TaigaCustomAttribute(BaseModel):
    name: str
    description: str
    type: Literal[
        "text", "multiline", "richtext", "date", "url", "dropdown", "checkbox", "number"
    ]
    order: int
    created_date: datetime
    modified_date: datetime = None

    model_config = ConfigDict(extra="allow")


class _TaigaMembership(BaseModel):
    user: EmailStr | None = None
    invited_by: EmailStr | None = None

    role: str | None  # related name

    is_admin: bool
    email: EmailStr | Literal[""] | None
    created_at: datetime
    invitation_extra_text: str | None
    user_order: int

    model_config = ConfigDict(extra="allow")


_UniqueTaigaMemberships = Annotated[
    list[_TaigaMembership], AfterValidator(UniqueInListValidator("user"))
]


class _TaigaMilestone(BaseModel):
    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None

    name: str
    slug: str
    estimated_start: datetime = None
    estimated_finish: datetime = None
    created_date: datetime
    modified_date: datetime = None
    closed: bool
    disponibility: float | None
    order: int

    model_config = ConfigDict(extra="allow")


class _TaigaTask(BaseModel):
    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None
    assigned_to: EmailStr | None = None

    status: str | None  # related name
    user_story: int | None = None  # related ref
    milestone: str | None = None  # related name

    created_date: datetime
    modified_date: datetime = None
    finished_date: datetime | None

    ref: int
    subject: str
    us_order: int
    taskboard_order: int
    description: str
    is_iocaine: bool
    external_reference: list[str] | None

    version: int
    is_blocked: bool
    blocked_note: str
    tags: list[str] | None

    due_date: datetime | None = None
    due_date_reason: str

    history: list[_TaigaHistory]
    attachments: list[_TaigaAttachment]
    custom_attributes_values: dict[str, _TaigaCustomAttributesValue]

    model_config = ConfigDict(extra="allow")


class _TaigaEpicRelatedUserStory(BaseModel):
    user_story: int | None  # related ref
    order: int
    source_project_slug: str | None = None  # related slug

    model_config = ConfigDict(extra="allow")


class _TaigaEpic(BaseModel):
    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None
    assigned_to: EmailStr | None = None

    ref: int
    status: str | None  # related name
    epics_order: int
    created_date: datetime
    modified_date: datetime = None
    subject: str
    description: str
    color: str  # hex code
    client_requirement: bool
    team_requirement: bool

    version: int
    is_blocked: bool
    blocked_note: str
    tags: list[str] | None

    related_user_stories: list[_TaigaEpicRelatedUserStory]

    history: list[_TaigaHistory]
    attachments: list[_TaigaAttachment]
    custom_attributes_values: dict[str, _TaigaCustomAttributesValue]

    model_config = ConfigDict(extra="allow")


class _TaigaRolePoints(BaseModel):
    role: str | None  # related slug
    points: str | None  # related slug


class _TaigaUserStory(BaseModel):
    tenzu_id: TenzuId | None = None

    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None
    assigned_to: EmailStr | None = None
    assigned_users: list[EmailStr | None] = (
        None  # usually also contains assigned_to, but there is no guarantee of that
    )
    status: str | None  # related name
    swimlane: str | None = None  # related name
    milestone: str | None = None  # related name
    role_points: list[_TaigaRolePoints] = None

    ref: int
    is_closed: bool
    backlog_order: int
    sprint_order: int
    kanban_order: int
    created_date: datetime
    modified_date: datetime = None
    finish_date: datetime | None = None
    subject: str
    description: str
    client_requirement: bool
    team_requirement: bool
    generated_from_issue: int | None = None  # related ref
    generated_from_task: int | None = None  # related ref
    from_task_ref: str | None
    external_reference: list[str] | None
    tribe_gig: Any | None

    version: int
    is_blocked: bool
    blocked_note: str
    tags: list[str] | None

    due_date: datetime | None = None
    due_date_reason: str

    history: list[_TaigaHistory]
    attachments: list[_TaigaAttachment]
    custom_attributes_values: dict[str, _TaigaCustomAttributesValue]

    model_config = ConfigDict(extra="allow")


class _TaigaIssue(BaseModel):
    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None
    assigned_to: EmailStr | None = None
    votes: list[EmailStr | None]

    status: str | None  # related name
    priority: str | None  # related name
    severity: str | None  # related name
    type: str | None  # related name
    milestone: str | None = None  # related name

    created_date: datetime
    modified_date: datetime = None
    finished_date: datetime | None

    ref: int | None
    subject: str
    description: str
    external_reference: list[str] | None

    version: int
    is_blocked: bool
    blocked_note: str
    tags: list[str] | None

    due_date: datetime | None = None
    due_date_reason: str

    history: list[_TaigaHistory]
    attachments: list[_TaigaAttachment]
    custom_attributes_values: dict[str, _TaigaCustomAttributesValue]

    model_config = ConfigDict(extra="allow")


class WikiPageExport(BaseModel):
    watchers: list[EmailStr | None] = None
    owner: EmailStr | None = None
    last_modifier: EmailStr | None = None

    slug: str
    created_date: datetime
    modified_date: datetime = None
    content: str

    version: int
    history: list[_TaigaHistory]
    attachments: list[_TaigaAttachment]

    model_config = ConfigDict(extra="allow")


class _TaigaWikiLink(BaseModel):
    title: str
    href: str
    order: int

    model_config = ConfigDict(extra="allow")


class _TaigaTimeline(BaseModel):
    data: dict
    data_content_type: tuple[str, str]
    event_type: str
    created: datetime

    model_config = ConfigDict(extra="allow")


class FullTaigaProjectImport(BaseModel):
    owner: EmailStr | None = None
    watchers: list[EmailStr | None] = None

    name: str
    slug: str
    description: str
    logo: _TaigaFile | None = None
    created_date: datetime
    modified_date: datetime | None = None
    total_milestones: int | None
    total_story_points: float | None
    is_epics_activated: bool
    is_backlog_activated: bool
    is_kanban_activated: bool
    is_wiki_activated: bool
    is_issues_activated: bool
    videoconferences: str | None
    videoconferences_extra_data: str | None
    is_private: bool
    is_featured: bool
    is_looking_for_people: bool
    looking_for_people_note: str
    epics_csv_uuid: str | None
    userstories_csv_uuid: str | None
    tasks_csv_uuid: str | None
    issues_csv_uuid: str | None
    transfer_token: str | None
    blocked_code: str | None
    anon_permissions: list[_TaigaAnonPermission] | None = None
    public_permissions: list[_TaigaMemberPermission] | None = None

    totals_updated_datetime: datetime
    total_fans: NonNegativeInt
    total_fans_last_week: NonNegativeInt
    total_fans_last_month: NonNegativeInt
    total_fans_last_year: NonNegativeInt
    total_activity: NonNegativeInt
    total_activity_last_week: NonNegativeInt
    total_activity_last_month: NonNegativeInt
    total_activity_last_year: NonNegativeInt

    tags_colors: list[tuple[str | None, str | None]] = None
    tags: list[str] | None

    creation_template: str | None = None  # related slug
    default_points: str | None = None  # related name
    default_epic_status: str | None = None  # related name
    default_us_status: str | None = None  # related name
    default_task_status: str | None = None  # related name
    default_priority: str | None = None  # related name
    default_severity: str | None = None  # related name
    default_issue_status: str | None = None  # related name
    default_issue_type: str | None = None  # related name
    default_swimlane: str | None = None  # related name

    roles: _UniqueTaigaRoles = None
    memberships: _UniqueTaigaMemberships = None
    points: list[_TaigaPoints] = None
    epic_statuses: list[_TaigaStatus] = None
    us_statuses: _UniqueTaigaUserStoryStatuses = None
    us_duedates: list[_TaigaDueDate] = None
    task_statuses: list[_TaigaStatus] = None
    task_duedates: list[_TaigaDueDate] = None
    issue_types: list[_TaigaIssueType] = None
    issue_statuses: list[_TaigaStatus] = None
    issue_duedates: list[_TaigaDueDate] = None
    priorities: list[_TaigaPriority] = None
    severities: list[_TaigaSeverity] = None
    swimlanes: _UniqueTaigaSwimlanes = None
    epiccustomattributes: list[_TaigaCustomAttribute] = None
    userstorycustomattributes: list[_TaigaCustomAttribute] = None
    taskcustomattributes: list[_TaigaCustomAttribute] = None
    issuecustomattributes: list[_TaigaCustomAttribute] = None
    epics: list[_TaigaEpic] = None
    user_stories: list[_TaigaUserStory] = None
    tasks: list[_TaigaTask] = None
    milestones: list[_TaigaMilestone] = None
    issues: list[_TaigaIssue] = None
    wiki_links: list[_TaigaWikiLink] = None
    wiki_pages: list[WikiPageExport] = None
    timeline: list[_TaigaTimeline]

    model_config = ConfigDict(extra="allow")

    def get_unknown_fields(self) -> Iterable[str]:
        """
        Return received keys that are not part of this serializer
        """
        return self.__pydantic_extra__.values() if self.__pydantic_extra__ else ()
