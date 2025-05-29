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
import logging
from typing import Any, TypeVar
from uuid import UUID

from django.conf import settings

from base.utils import emails
from base.utils.datetime import aware_utcnow
from memberships import repositories as memberships_repositories
from memberships.choices import InvitationStatus
from memberships.models import Invitation, Membership, Role
from memberships.services import exceptions as ex
from projects.projects.models import Project
from users import services as users_services
from users.models import AnyUser, User
from workspaces.workspaces.models import Workspace

logger = logging.getLogger(__name__)

TM = TypeVar("TM", bound=Membership)
TI = TypeVar("TI", bound=Invitation)

##########################################################
# update membership
##########################################################


async def update_membership(membership: TM, role_id: UUID, user_role: Role) -> TM:
    try:
        role = await memberships_repositories.get_role(
            membership.role.__class__,
            filters={**membership.reference_model_filter, "id": role_id},
        )

    except membership.role.DoesNotExist as e:
        raise ex.NonExistingRoleError("Role does not exist") from e

    if not role.is_owner:
        if await is_membership_the_only_owner(membership):
            raise ex.MembershipIsTheOnlyOwnerError("Membership is the only owner")
    elif not user_role or not user_role.is_owner:
        raise ex.OwnerRoleNotAuthorisedError(
            "You don't have the permissions to promote a membership to owner"
        )

    updated_membership = await memberships_repositories.update_membership(
        membership=membership,
        values={"role": role},
    )

    return updated_membership


##########################################################
# misc membership
##########################################################


async def is_membership_the_only_owner(membership: TM) -> bool:
    if not membership.role.is_owner:
        return False

    return not await memberships_repositories.has_other_owner_memberships(
        membership=membership
    )


##########################################################
# create invitations
##########################################################


async def create_invitations(
    reference_object: Project | Workspace,
    invitations: list[dict[str, str | UUID]],
    invited_by: User,
    user_role: Role,
) -> tuple[list[TI], list[TI], int]:
    # create two lists with roles_slug and the emails received (either directly by the invitation's email, or by the
    # invited username's email)
    already_members = 0
    emails: list[str] = []
    emails_roles: list[str] = []
    usernames: list[str] = []
    usernames_roles: list[str] = []
    for i in invitations:
        if i.get("username"):
            usernames.append(i["username"])
            usernames_roles.append(i["role_id"])

        elif i.get("email"):
            emails.append(i["email"].lower())
            emails_roles.append(i["role_id"])
    # emails =    ['user1@tenzu.demo']  |  emails_roles =    [<member_role_uuid>]
    # usernames = ['user3']             |  usernames_roles = [<admin_role_uuid>]
    invitation_role_ids = set(emails_roles + usernames_roles)

    roles_dict = {
        r.id: r
        for r in await memberships_repositories.list_roles(
            reference_object.roles.model,
            filters={
                f"{reference_object._meta.model_name}_id": reference_object.id,
                "id__in": invitation_role_ids,
            },
        )
    }
    # roles_dict = {<admin_role_uuid>: <Role: Administrator>, <member_role_uuid>: <Role: Member>}
    wrong_roles_ids = invitation_role_ids - roles_dict.keys()
    if wrong_roles_ids:
        raise ex.NonExistingRoleError(f"These role ids don't exist: {wrong_roles_ids}")

    users_emails_dict: dict[str, Any] = {}
    if len(emails) > 0:
        users_emails_dict = await users_services.list_users_emails_as_dict(
            emails=emails
        )
    # users_emails_dict = {
    #   'user1@tenzu.demo': <User: Norma Fisher>,
    #   'user3@tenzu.demo': <User: Elisabeth Woods>,
    # }
    users_usernames_dict: dict[str, Any] = {}
    if len(usernames) > 0:
        users_usernames_dict = await users_services.list_users_usernames_as_dict(
            usernames=usernames
        )
        # users_usernames_dict = {
        #   'user3': <User: Elizabeth Woods>,
        # }
        # all usernames should belong to a user; otherwise it's an error
        if len(users_usernames_dict) < len(usernames):
            wrong_usernames = set(usernames) - users_usernames_dict.keys()
            raise ex.InvitationNonExistingUsernameError(
                f"These usernames don't exist: {wrong_usernames}"
            )

    invitations_to_create: dict[str, Invitation] = {}
    invitations_to_update: dict[str, Invitation] = {}
    invitations_to_send: dict[str, Invitation] = {}
    members = await memberships_repositories.list_members(
        reference_object=reference_object
    )

    users_dict = users_emails_dict | users_usernames_dict
    # users_dict = {
    #         'user1@tenzu.demo': <User: Norma Fisher>,
    #         'user3': <User: Elizabeth Woods>,
    #         'user3@tenzu.demo': <User: Elizabeth Woods>,
    # }
    created_owner_invitations = []
    changed_role_owner_invitations = []
    already_accepted_invitations = []

    for key, role_id in zip(emails + usernames, emails_roles + usernames_roles):
        #                                 key  |  role_id
        # ==========================================================
        # (1st iteration)   'user1@tenzu.demo' | <member_role_uuid>
        # (2nd iteration)              'user3' | <admin_role_uuid>

        user = users_dict.get(key)
        if user and user in members:
            already_members += 1
            continue
        email = user.email if user else key
        role = roles_dict[role_id]

        try:
            invitation = await memberships_repositories.get_invitation(
                reference_object.invitations.model,
                filters={
                    f"{reference_object._meta.model_name}_id": reference_object.id,
                },
                q_filter=memberships_repositories.invitation_username_or_email_query(
                    email
                ),
                select_related=[
                    "user",
                    "role",
                ],
            )
        except reference_object.invitations.model.DoesNotExist:
            new_invitation = reference_object.invitations.model(
                user=user,
                role=role,
                email=email,
                invited_by=invited_by,
                **{reference_object._meta.model_name: reference_object},
            )
            invitations_to_create[email] = new_invitation
            invitations_to_send[email] = new_invitation
            if role.is_owner:
                created_owner_invitations.append(key)
        else:
            if invitation.status == InvitationStatus.ACCEPTED:
                # weird state where user is not member but still has an accepted invitation, shouldn't happen ever
                logger.error(
                    f"Trying to create already accepted invitation {invitation._meta.model_name} {invitation.id}"
                )
                already_accepted_invitations.append(invitation)
                continue
            if invitation.role.is_owner and invitation.role != role:
                changed_role_owner_invitations.append(key)
            invitation.role = role
            invitation.status = InvitationStatus.PENDING
            if not is_spam(invitation):
                invitation.num_emails_sent += 1
                invitation.resent_at = aware_utcnow()
                invitation.resent_by = invited_by
                invitations_to_send[email] = invitation
            invitations_to_update[email] = invitation

    if already_accepted_invitations:
        raise ex.InvitationAlreadyAcceptedError(
            f"Cannot recreate an accepted invitation: {', '.join(invitation.email for invitation in already_accepted_invitations)}"
        )
    if (created_owner_invitations or changed_role_owner_invitations) and (
        not user_role or not user_role.is_owner
    ):
        detail_msg = []
        if created_owner_invitations:
            detail_msg.append(
                f"give owner role to invitations {', '.join(created_owner_invitations)}"
            )

        if changed_role_owner_invitations:
            detail_msg.append(
                f"remove owner role from existing invitations {', '.join(changed_role_owner_invitations)}"
            )

        raise ex.OwnerRoleNotAuthorisedError(
            f"You dont have permissions to: {' / '.join(detail_msg)}"
        )
    if len(invitations_to_update) > 0:
        objs = list(invitations_to_update.values())
        await memberships_repositories.bulk_update_invitations(
            reference_object.invitations.model,
            objs_to_update=objs,
            fields_to_update=[
                "role",
                "num_emails_sent",
                "resent_at",
                "resent_by",
                "status",
            ],
        )

    if len(invitations_to_create) > 0:
        objs = list(invitations_to_create.values())
        await memberships_repositories.create_invitations(
            reference_object.invitations.model, objs=objs
        )

    invitations_to_publish = []
    if len(invitations_to_create) > 0 or len(invitations_to_update) > 0:
        invitations_to_publish = list(
            (invitations_to_create | invitations_to_update).values()
        )

    return list(invitations_to_send.values()), invitations_to_publish, already_members


##########################################################
# update invitations
##########################################################


async def update_invitation(
    invitation: TI,
    role_id: UUID,
    user_role: Role,
) -> TI:
    if invitation.status == InvitationStatus.ACCEPTED:
        raise ex.InvitationAlreadyAcceptedError(
            "Cannot change role in an accepted invitation"
        )

    if invitation.status == InvitationStatus.DENIED:
        raise ex.InvitationDeniedError("The invitation has already been denied")

    if invitation.status == InvitationStatus.REVOKED:
        raise ex.InvitationRevokedError("The invitation has already been revoked")

    try:
        role = await memberships_repositories.get_role(
            invitation.role.__class__,
            filters={**invitation.reference_model_filter, "id": role_id},
        )

    except invitation.role.DoesNotExist as e:
        raise ex.NonExistingRoleError("Role does not exist") from e

    if role.is_owner and (not user_role or not user_role.is_owner):
        raise ex.OwnerRoleNotAuthorisedError(
            "You don't have the permissions to promote an invitation to owner"
        )

    updated_invitation = await memberships_repositories.update_invitation(
        invitation=invitation,
        values={"role": role},
    )

    return updated_invitation


##########################################################
# accept invitation
##########################################################


async def accept_invitation(invitation: TI) -> TI:
    if invitation.status == InvitationStatus.ACCEPTED:
        raise ex.InvitationAlreadyAcceptedError(
            "The invitation has already been accepted"
        )

    if invitation.status == InvitationStatus.DENIED:
        raise ex.InvitationDeniedError("The invitation is denied")

    if invitation.status == InvitationStatus.REVOKED:
        raise ex.InvitationRevokedError("The invitation is revoked")

    if not invitation.user:
        raise ex.InvitationHasNoUserYetError("The invitation does not have a user yet")

    accepted_invitation = await memberships_repositories.update_invitation(
        invitation=invitation,
        values={"status": InvitationStatus.ACCEPTED},
    )

    return accepted_invitation


##########################################################
# resend invitation
##########################################################


async def resend_invitation(invitation: TI, resent_by: User) -> TI | None:
    if invitation.status == InvitationStatus.ACCEPTED:
        raise ex.InvitationAlreadyAcceptedError("Cannot resend an accepted invitation")

    if invitation.status == InvitationStatus.DENIED:
        raise ex.InvitationDeniedError("The invitation has already been denied")

    if invitation.status == InvitationStatus.REVOKED:
        raise ex.InvitationRevokedError("The invitation has already been revoked")

    if not is_spam(invitation):
        num_emails_sent = invitation.num_emails_sent + 1
        resent_invitation = await memberships_repositories.update_invitation(
            invitation=invitation,
            values={
                "num_emails_sent": num_emails_sent,
                "resent_at": aware_utcnow(),
                "resent_by": resent_by,
            },
        )
        return resent_invitation
    return None


##########################################################
# deny invitation
##########################################################


async def deny_invitation(invitation: TI) -> TI:
    if not invitation.user:
        raise ex.InvitationHasNoUserYetError("The invitation does not have a user yet")

    if invitation.status == InvitationStatus.ACCEPTED:
        raise ex.InvitationAlreadyAcceptedError("Cannot deny an accepted invitation")

    if invitation.status == InvitationStatus.REVOKED:
        raise ex.InvitationRevokedError("Cannot deny a revoked invitation")

    if invitation.status == InvitationStatus.DENIED:
        raise ex.InvitationDeniedError("The invitation has already been denied")

    denied_invitation = await memberships_repositories.update_invitation(
        invitation=invitation,
        values={
            "status": InvitationStatus.DENIED,
        },
    )

    return denied_invitation


##########################################################
# revoke invitation
##########################################################


async def revoke_invitation(invitation: TI, revoked_by: User) -> TI:
    if invitation.status == InvitationStatus.ACCEPTED:
        raise ex.InvitationAlreadyAcceptedError("Cannot revoke an accepted invitation")

    if invitation.status == InvitationStatus.DENIED:
        raise ex.InvitationDeniedError("Cannot revoke a denied invitation")

    if invitation.status == InvitationStatus.REVOKED:
        raise ex.InvitationRevokedError("The invitation has already been revoked")

    revoked_invitation = await memberships_repositories.update_invitation(
        invitation=invitation,
        values={
            "status": InvitationStatus.REVOKED,
            "revoked_at": aware_utcnow(),
            "revoked_by": revoked_by,
        },
    )

    return revoked_invitation


##########################################################
# misc invitation
##########################################################


def is_spam(invitation: TI) -> bool:
    last_send_at = (
        invitation.resent_at if invitation.resent_at else invitation.created_at
    )
    time_since_last_send = int(
        (aware_utcnow() - last_send_at).total_seconds() / 60
    )  # in minutes
    return (
        invitation.num_emails_sent
        >= settings.INVITATION_RESEND_LIMIT  # max invitations emails already sent
        or time_since_last_send
        < settings.INVITATION_RESEND_TIME  # too soon to send the invitation again
    )


def is_invitation_for_this_user(invitation: TI, user: User) -> bool:
    """
    Check if a  invitation if for an specific user
    """
    return emails.are_the_same(user.email, invitation.email)


async def has_pending_invitation(
    user: AnyUser, reference_object: Project | Workspace
) -> bool:
    if user.is_anonymous:
        return False

    return await memberships_repositories.exists_invitation(
        reference_object.invitations.model,
        filters={
            f"{reference_object._meta.model_name}_id": reference_object.id,
        },
        q_filter=memberships_repositories.pending_user_invitation_query(user),
    )
