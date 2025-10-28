# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final
from uuid import UUID

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Model
from faker import Faker
from ninja import UploadedFile

from base.sampledata import constants
from comments.models import Comment
from commons.colors import NUM_COLORS
from commons.ordering import DEFAULT_ORDER_OFFSET
from memberships.choices import InvitationStatus
from ninja_jwt.utils import aware_utcnow
from projects.invitations import repositories as pj_invitations_repositories
from projects.invitations.models import ProjectInvitation
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.projects import services as projects_services
from projects.projects.models import Project
from projects.references import get_new_project_reference_id
from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from users.models import User
from workflows.models import WorkflowStatus
from workspaces.invitations import repositories as ws_invitations_repositories
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.workspaces import services as workspaces_services
from workspaces.workspaces.models import Workspace

fake: Faker = Faker()
Faker.seed(0)
random.seed(0)


MEDIA_DIR: Final[Path] = Path(__file__).parent.joinpath("media")
PROJECT_LOGOS_DIR: Final[Path] = MEDIA_DIR.joinpath("projects")


################################
# USERS
################################


async def create_user(
    username: str,
    full_name: str | None = None,
    email: str | None = None,
    color: int | None = None,
) -> User:
    acceptance_date = aware_utcnow() if settings.REQUIRED_TERMS else None
    user = User(
        username=username,
        full_name=full_name or fake.name(),
        email=email or f"{username}@tenzu.demo",
        color=color or fake.random_int(min=1, max=NUM_COLORS),
        is_active=True,
        accepted_terms_of_service=acceptance_date,
        accepted_privacy_policy=acceptance_date,
    )
    user.set_password("123123")
    await user.asave()
    return user


################################
# WORKSPACES
################################


async def create_workspace(
    created_by: User, name: str | None = None, color: int | None = None
) -> Workspace:
    return (
        await workspaces_services._create_workspace(
            name=name or fake.bs()[:35],
            color=color or fake.random_int(min=1, max=NUM_COLORS),
            created_by=created_by,
        )
    )[0]


async def create_workspace_memberships(workspace: Workspace, users: list[User]) -> None:
    # get users except the creator of the workspace
    users_without_creator = [u for u in users if u.id != workspace.created_by_id]
    roles = [role async for role in workspace.roles.all()]
    owner_role = [r for r in roles if r.is_owner][0]
    other_roles = [r for r in roles if not r.is_owner]

    memberships = await WorkspaceMembership.objects.abulk_create(
        [
            WorkspaceMembership(
                user=user, workspace=workspace, role=random.choice(other_roles)
            )
            for user in users_without_creator
        ]
    )
    # hack to fill prefetch cache so that no db refresh is needed to sync memberships
    workspace._prefetched_objects_cache = {"roles": roles}
    workspace._prefetched_objects_cache["memberships"] = [
        WorkspaceMembership(
            user=workspace.created_by, workspace=workspace, role=owner_role
        ),
        *memberships,
    ]
    workspace._prefetched_objects_cache["members"] = users


async def create_workspace_membership(
    user: User, workspace: Workspace, role: WorkspaceRole
):
    await ws_memberships_repositories.create_workspace_membership(
        user=user, workspace=workspace, role=role
    )
    await create_workspace_invitation(
        user=user, workspace=workspace, role=role, status=InvitationStatus.ACCEPTED
    )


async def create_workspace_invitations(
    workspace: Workspace, invitees: list[User]
) -> None:
    # add accepted invitations for workspace memberships
    invitations = [
        WorkspaceInvitation(
            user=m.user,
            workspace=workspace,
            role=m.role,
            email=m.user.email,
            status=InvitationStatus.ACCEPTED,
            invited_by=workspace.created_by,
        )
        for m in workspace.memberships.all()
        if m.user_id != workspace.created_by_id
    ]

    random.shuffle(invitees)

    # get workspace roles
    roles = list(workspace.roles.all())

    # add between 0 and 5 pending invitations for registered users
    num_invitees = random.randint(0, 5)
    for user in invitees[:num_invitees]:
        invitations.append(
            WorkspaceInvitation(
                user=user,
                workspace=workspace,
                role=random.choice(roles),
                email=user.email,
                status=InvitationStatus.PENDING,
                invited_by=workspace.created_by,
            )
        )

    # add 0, 1 or 2 pending invitations for unregistered users
    num_invitees = random.randint(0, 2)
    for i in range(num_invitees):
        invitations.append(
            WorkspaceInvitation(
                user=None,
                workspace=workspace,
                role=random.choice(roles),
                email=f"email-{i}@email.com",
                status=InvitationStatus.PENDING,
                invited_by=workspace.created_by,
            )
        )

    # create invitations in bulk
    await ws_invitations_repositories.create_invitations(
        WorkspaceInvitation, objs=invitations
    )


async def create_workspace_invitation(
    user: User,
    workspace: Workspace,
    role: WorkspaceRole,
    status=InvitationStatus.PENDING,
):
    return await WorkspaceInvitation.objects.acreate(
        user=user, email=user.email, workspace=workspace, role=role, status=status
    )


################################
# PROJECTS
################################


async def get_project_with_related_info(id: UUID) -> Project:
    return await (
        Project.objects.select_related(
            "created_by",
            "workspace",
        )
        .prefetch_related(
            "roles",
            "members",
            "memberships",
            "memberships__user",
            "memberships__role",
            "workflows",
            "workflows__statuses",
        )
        .aget(id=id)
    )


async def create_project(
    workspace: Workspace,
    created_by: User,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    name = name or fake.catch_phrase()
    description = description or fake.paragraph(nb_sentences=2)
    logo = random.choice(list(PROJECT_LOGOS_DIR.iterdir()))

    with logo.open("rb") as file:
        logo_file = (
            UploadedFile(file=file, name=logo.name)
            if fake.boolean(chance_of_getting_true=constants.PROB_PROJECT_WITH_LOGO)
            else None
        )
        return await projects_services._create_project(
            name=name,
            description=description,
            color=fake.random_int(min=1, max=NUM_COLORS),
            created_by=created_by,
            workspace=workspace,
            logo_file=logo_file,
        )


async def create_project_memberships(project: Project, users: list[User]) -> None:
    # get owner and other roles
    other_roles = [r for r in project.roles.all() if not r.is_owner]
    owner_role = [r for r in project.roles.all() if r.is_owner][0]
    memberships_cache = [
        ProjectMembership(user=project.created_by, project=project, role=owner_role)
    ]

    users_without_creator = [u for u in users if u.id != project.created_by_id]

    # calculate owner (at least 1/3 of the members) and no owner users
    num_owners = random.randint(0, len(users_without_creator) // 3)
    for user in users_without_creator[:num_owners]:
        memberships_cache.append(
            await pj_memberships_repositories.create_project_membership(
                user=user, project=project, role=owner_role
            )
        )

    if other_roles:
        for user in users_without_creator[num_owners:]:
            role = random.choice(other_roles)
            memberships_cache.append(
                await pj_memberships_repositories.create_project_membership(
                    user=user, project=project, role=role
                )
            )
    # hack to fill prefetch cache so that no db refresh is needed to sync memberships
    project._prefetched_objects_cache["memberships"] = memberships_cache
    project._prefetched_objects_cache["members"] = users


async def create_project_membership(user: User, project: Project, role: ProjectRole):
    await pj_memberships_repositories.create_project_membership(
        user=user, project=project, role=role
    )
    await create_project_invitation(
        user=user, project=project, role=role, status=InvitationStatus.ACCEPTED
    )


async def create_project_invitations(project: Project, invitees: list[User]) -> None:
    # add accepted invitations for project memberships
    invitations = [
        ProjectInvitation(
            user=m.user,
            project=project,
            role=m.role,
            email=m.user.email,
            status=InvitationStatus.ACCEPTED,
            invited_by=project.created_by,
        )
        for m in project.memberships.all()
        if m.user_id != project.created_by_id
    ]

    random.shuffle(invitees)

    # get project roles
    roles = list(project.roles.all())

    # add between 0 and 5 pending invitations for registered users
    num_invitees = random.randint(0, 5)
    for user in invitees[:num_invitees]:
        invitations.append(
            ProjectInvitation(
                user=user,
                project=project,
                role=random.choice(roles),
                email=user.email,
                status=InvitationStatus.PENDING,
                invited_by=project.created_by,
            )
        )

    # add 0, 1 or 2 pending invitations for unregistered users
    num_invitees = random.randint(0, 2)
    for i in range(num_invitees):
        invitations.append(
            ProjectInvitation(
                user=None,
                project=project,
                role=random.choice(roles),
                email=f"email-{i}@email.com",
                status=InvitationStatus.PENDING,
                invited_by=project.created_by,
            )
        )

    # create invitations in bulk
    await pj_invitations_repositories.create_invitations(
        ProjectInvitation, objs=invitations
    )


async def create_project_invitation(
    user: User, project: Project, role: ProjectRole, status=InvitationStatus.PENDING
):
    return await ProjectInvitation.objects.acreate(
        user=user, email=user.email, project=project, role=role, status=status
    )


#################################
# STORIES
#################################


async def create_stories(
    project: Project,
    min_stories: int = constants.NUM_STORIES_PER_WORKFLOW[0],
    max_stories: int | None = None,
    with_comments: bool = False,
) -> None:
    num_stories_to_create = fake.random_int(
        min=min_stories,
        max=max_stories or min_stories or constants.NUM_STORIES_PER_WORKFLOW[1],
    )
    members = list(project.members.all())
    workflows = list(project.workflows.all())

    # Create stories
    stories = []
    for workflow in workflows:
        statuses = list(workflow.statuses.all())

        for i in range(num_stories_to_create):
            status_index = random.randint(0, len(statuses) - 1)
            stories.append(
                await _create_story(
                    status=statuses[status_index],
                    created_by=random.choice(members),
                    # first N stories will be spaced using offset, others will not (to easily test for edge cases)
                    order=DEFAULT_ORDER_OFFSET * (status_index + 1) * i
                    if i < DEFAULT_ORDER_OFFSET
                    else DEFAULT_ORDER_OFFSET
                    * (status_index + 1)
                    * DEFAULT_ORDER_OFFSET
                    + i,
                    save=False,
                )
            )
        await Story.objects.abulk_create(stories)

    # Create story assignments and comments
    story_assignments = []
    async for story in Story.objects.select_related().filter(project=project):
        if fake.random_number(digits=2) < constants.PROB_STORY_ASSIGNMENTS.get(
            story.status.name, constants.PROB_STORY_ASSIGNMENTS_DEFAULT
        ):
            # Sometimes we assign all the members
            members_sample = (
                members
                if fake.boolean(chance_of_getting_true=10)
                else fake.random_sample(elements=members)
            )
            for member in members_sample:
                story_assignments.append(
                    StoryAssignment(
                        story=story,
                        user=member,
                        created_at=fake.date_time_between(
                            start_date=story.created_at, tzinfo=timezone.utc
                        ),
                    )
                )

        # Create story comments
        if with_comments:
            await create_story_comments(
                story=story,
                status_name=story.status.name,
                pj_members=members,
            )

    await StoryAssignment.objects.abulk_create(story_assignments)


async def _create_story(
    status: WorkflowStatus,
    created_by: User,
    order: int,
    title: str | None = None,
    description: str | None = None,
    save: bool = True,
) -> Story:
    _ref = await sync_to_async(get_new_project_reference_id)(status.workflow.project_id)
    _title = (
        title
        or fake.text(max_nb_chars=random.choice(constants.STORY_TITLE_MAX_SIZE))[:500]
    )
    _description = (
        description
        or '[{"id":"1166453f-52f7-4dea-af18-245e5d05e9a6","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azerazerazer","styles":{}}],"children":[]},{"id":"32fb12dd-e776-4831-8dd6-16c96026b313","type":"heading","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left","level":1,"isToggleable":false},"content":[{"type":"text","text":"qsdfqdsf","styles":{}}],"children":[]},{"id":"a8d6fe16-3f18-4f71-982c-69ba5732cdc2","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"c\'est ma story","styles":{}}],"children":[]},{"id":"4c0b279e-9de7-4667-8dbc-edee05e342e1","type":"table","props":{"textColor":"default"},"content":{"type":"tableContent","columnWidths":[null,null],"rows":[{"cells":[{"type":"tableCell","content":[{"type":"text","text":"zazer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[{"type":"text","text":"azer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]},{"cells":[{"type":"tableCell","content":[{"type":"text","text":"zaer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]},{"cells":[{"type":"tableCell","content":[{"type":"text","text":"azer","styles":{}}],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}},{"type":"tableCell","content":[],"props":{"colspan":1,"rowspan":1,"backgroundColor":"default","textColor":"default","textAlignment":"left"}}]}]},"children":[]},{"id":"2ccaa64b-33fe-4a75-b992-5198531e5dc4","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azerazer","styles":{}}],"children":[]},{"id":"7a4b3bb2-8d4a-46d5-afc4-43f25b17c7e9","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"fc1482af-5f64-4438-a612-986bbcfd7b43","type":"paragraph","props":{"textColor":"orange","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"aze","styles":{}}],"children":[]},{"id":"3cbd9ebc-bd6b-4248-bdef-a096cffad5d2","type":"paragraph","props":{"textColor":"green","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"r","styles":{}}],"children":[]},{"id":"2f00a347-ac78-4a47-93dc-78d527ff629e","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"az","styles":{}}],"children":[]},{"id":"5dfc1eb7-d4a0-4dbd-a9fe-8bfb6b7b2777","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"er","styles":{}}],"children":[]},{"id":"e8e15a81-1a7b-444b-b85c-a3fe65df91e4","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"7ad4cb1a-11f9-484f-a8f4-840047031782","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"azer","styles":{}}],"children":[]},{"id":"58835732-f4d6-400c-a9be-c73d14822959","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"639c8f05-f455-4ebb-9cb2-d2a80b9bf779","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"aze","styles":{}}],"children":[]},{"id":"1b083741-979c-446c-b665-4f717f48807e","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"r","styles":{}}],"children":[]},{"id":"fad89674-19ef-4208-8d57-59c4fafc9562","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"zear","styles":{}}],"children":[]},{"id":"67650f81-0eca-44ad-b0a7-98ab8df54073","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"cbc53186-d7ca-48b0-9fba-bcd532c79807","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[{"type":"text","text":"zaer","styles":{}}],"children":[]},{"id":"d93922cb-6de9-4e86-8326-59752b056cf1","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]},{"id":"727a4c8d-9443-4304-9f13-5e20afaafd9c","type":"paragraph","props":{"textColor":"default","backgroundColor":"default","textAlignment":"left"},"content":[],"children":[]}]'
    )
    _created_at = fake.date_time_between(start_date="-2y", tzinfo=timezone.utc)

    story = Story(
        ref=_ref,
        title=_title,
        description=_description,
        order=order,
        created_at=_created_at,
        created_by_id=created_by.id,
        project_id=status.workflow.project_id,
        workflow_id=status.workflow_id,
        status_id=status.id,
    )
    if save:
        await sync_to_async(story.save)()
    return story


#################################
# COMMENTS
#################################


async def create_story_comments(
    story: Story, status_name: str, pj_members: list[User], text: str | None = None
) -> None:
    story_comments = []
    prob_comments = constants.PROB_STORY_COMMENTS.get(
        status_name, constants.PROB_STORY_COMMENTS_DEFAULT
    )
    if fake.random_number(digits=2) < prob_comments:
        max_comments = constants.PROB_STORY_COMMENTS.get(
            status_name, constants.PROB_STORY_COMMENTS_DEFAULT
        )
        for _ in range(fake.random_int(min=1, max=max_comments)):
            story_comments.append(
                await _create_comment_object(
                    text=text
                    if text
                    else f'[{{"id":"ecef7c0e-8c64-4657-bd5f-642c2b386404","type":"paragraph","props":{{"textColor":"default","backgroundColor":"default","textAlignment":"left"}},"content":[{{"type":"text","text":"{fake.paragraph(nb_sentences=2)}","styles":{{}},"children":[]}}]}}]',
                    created_by=fake.random_element(elements=pj_members),
                    object=story,
                )
            )
    await Comment.objects.abulk_create(story_comments)


@sync_to_async
def _create_comment_object(
    text: str,
    created_by: User,
    object: Model,
    created_at: datetime | None = None,
) -> Comment:
    comment = Comment(
        text=text,
        content_object=object,
        created_by=created_by,
        created_at=(
            created_at
            if created_at
            else fake.date_time_between(
                start_date=object.created_at,  # type: ignore[attr-defined]
                tzinfo=timezone.utc,
                end_date=object.created_at
                + timedelta(days=constants.MAX_DAYS_LAST_COMMENT),  # type: ignore[attr-defined]
            )
        ),
    )

    if fake.boolean(chance_of_getting_true=constants.PROB_MODIFIED_COMMENT):
        comment.modified_at = fake.date_time_between(
            start_date=comment.created_at, tzinfo=timezone.utc
        )

    if fake.boolean(chance_of_getting_true=constants.PROB_DELETED_COMMENT):
        comment.text = ""
        comment.deleted_at = fake.date_time_between(
            start_date=comment.modified_at or comment.created_at, tzinfo=timezone.utc
        )
        comment.deleted_by = comment.created_by

    return comment
