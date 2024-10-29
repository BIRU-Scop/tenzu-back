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

from events.actions import CheckProjectEventsSubscriptionAction, CheckWorkspaceEventsSubscriptionAction

__all__ = [
    "emit_event_action_to_check_project_subscription",
    "emit_event_action_to_check_workspace_subscription",
]


async def emit_event_action_to_check_project_subscription(project_b64id: str) -> None:
    from events import events_manager

    await events_manager.publish_on_project_channel(
        project=project_b64id,
        type="action",
        content=CheckProjectEventsSubscriptionAction(project=project_b64id),
    )


async def emit_event_action_to_check_workspace_subscription(
    workspace_b64id: str,
) -> None:
    from events import events_manager

    await events_manager.publish_on_workspace_channel(
        workspace=workspace_b64id,
        type="action",
        content=CheckWorkspaceEventsSubscriptionAction(workspace=workspace_b64id),
    )
