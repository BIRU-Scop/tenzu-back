# -*- coding: utf-8 -*-
# Copyright (C) 2024 BIRU
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
from django.db.models import Model
from faker import Faker
from ninja import UploadedFile

from base.sampledata import constants
from comments.models import Comment
from commons.colors import NUM_COLORS
from commons.ordering import DEFAULT_ORDER_OFFSET
from memberships.choices import InvitationStatus
from projects.invitations import repositories as pj_invitations_repositories
from projects.invitations.models import ProjectInvitation
from projects.memberships import repositories as pj_memberships_repositories
from projects.memberships.models import ProjectRole
from projects.projects import services as projects_services
from projects.projects.models import Project
from projects.references import get_new_project_reference_id
from stories.assignments.models import StoryAssignment
from stories.stories.models import Story
from users.models import User
from workflows.models import WorkflowStatus
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.memberships import services as ws_memberships_services
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


@sync_to_async
def create_user(
    username: str,
    full_name: str | None = None,
    email: str | None = None,
    color: int | None = None,
) -> User:
    user = User.objects.create(
        username=username,
        full_name=full_name or fake.name(),
        email=email or f"{username}@tenzu.demo",
        color=color or fake.random_int(min=1, max=NUM_COLORS),
        is_active=True,
    )
    user.set_password("123123")
    user.save()
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
    users = [u for u in users if u.id != workspace.created_by_id]
    role = await ws_memberships_services.get_workspace_role(workspace.id, "member")

    await WorkspaceMembership.objects.abulk_create(
        [
            WorkspaceMembership(user=user, workspace=workspace, role=role)
            for user in users
        ]
    )


async def create_workspace_invitation(
    user: User, workspace: Workspace, role: WorkspaceRole
):
    return await WorkspaceInvitation.objects.acreate(
        user=user, email=user.email, workspace=workspace, role=role
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
    memberships_cache = []
    # get owner and other roles
    other_roles = [r for r in project.roles.all() if r.slug != "owner"]
    owner_role = [r for r in project.roles.all() if r.slug == "owner"][0]

    # get users except the creator of the project
    users = [u for u in users if u.id != project.created_by_id]

    # calculate owner (at least 1/3 of the members) and no owner users
    num_owners = random.randint(0, len(users) // 3)
    for user in users[:num_owners]:
        memberships_cache.append(
            await pj_memberships_repositories.create_project_membership(
                user=user, project=project, role=owner_role
            )
        )

    if other_roles:
        for user in users[num_owners:]:
            role = random.choice(other_roles)
            memberships_cache.append(
                await pj_memberships_repositories.create_project_membership(
                    user=user, project=project, role=role
                )
            )
    # hack to fill prefetch cache so that no db refresh is needed to sync memberships
    project._prefetched_objects_cache["memberships"] = memberships_cache
    project._prefetched_objects_cache["members"] = [m.user for m in memberships_cache]


async def create_project_invitations(project: Project, users: list[User]) -> None:
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

    # get no members
    members = list(project.members.all())
    no_members = [u for u in users if u not in members]
    random.shuffle(no_members)

    # get project roles
    roles = list(project.roles.all())

    # add 0, 1 or 2 pending invitations for registered users
    num_users = random.randint(0, 2)
    for user in no_members[:num_users]:
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
    num_users = random.randint(0, 2)
    for i in range(num_users):
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


async def create_project_invitation(user: User, project: Project, role: ProjectRole):
    return await ProjectInvitation.objects.acreate(
        user=user, email=user.email, project=project, role=role
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
            stories.append(
                await _create_story(
                    status=random.choice(statuses),
                    created_by=random.choice(members),
                    # first N stories will be spaced using offset, others will not (to easily test for edge cases)
                    order=DEFAULT_ORDER_OFFSET * i
                    if i < DEFAULT_ORDER_OFFSET
                    else DEFAULT_ORDER_OFFSET * DEFAULT_ORDER_OFFSET + i,
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
        or '{"time":1727777794238,"blocks":[{"id":"7X6r-YHhqt","type":"paragraph","data":{"text":"azer"}},{"id":"45qpxXqs7u","type":"paragraph","data":{"text":"azer"}},{"id":"Im_opySj3l","type":"paragraph","data":{"text":"azerazer"}}],"version":"2.30.5"}'
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
                    text=text if text else f"<p>{fake.paragraph(nb_sentences=2)}</p>",
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
