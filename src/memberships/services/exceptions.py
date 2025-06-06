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

from base.services.exceptions import TenzuServiceException


class NonExistingRoleError(TenzuServiceException):
    pass


class MembershipWithRoleThatDoNotBelong(TenzuServiceException):
    pass


class SameSuccessorAsCurrentMember(TenzuServiceException):
    pass


class MembershipIsTheOnlyOwnerError(TenzuServiceException):
    pass


class ExistingProjectMembershipsError(TenzuServiceException):
    pass


class ExistingOwnerProjectMembershipsAndNotOwnerError(TenzuServiceException):
    pass


class NoRelatedWorkspaceMembershipsError(TenzuServiceException):
    pass


class NonEditableRoleError(TenzuServiceException):
    pass


class NotValidPermissionsSetError(TenzuServiceException):
    pass


class IncompatiblePermissionsSetError(TenzuServiceException):
    pass


class OwnerRoleNotAuthorisedError(TenzuServiceException):
    pass


class NonExistingMoveToRole(TenzuServiceException):
    pass


class SameMoveToRole(TenzuServiceException):
    pass


class RequiredMoveToRole(TenzuServiceException):
    pass


class RoleWithTargetThatDoNotBelong(TenzuServiceException):
    pass


# --- Invitations


class BadInvitationTokenError(TenzuServiceException):
    pass


class InvitationAlreadyAcceptedError(TenzuServiceException):
    pass


class InvitationDoesNotExistError(TenzuServiceException):
    pass


class InvitationIsNotForThisUserError(TenzuServiceException):
    pass


class InvitationRevokedError(TenzuServiceException):
    pass


class InvitationDeniedError(TenzuServiceException):
    pass


class InvitationHasNoUserYetError(TenzuServiceException):
    pass


class InvitationNonExistingUsernameError(TenzuServiceException):
    pass
