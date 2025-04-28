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

from django.db.models import Q


def Q_for_related(q: Q, related_field: str) -> Q:
    """
    copy a Q object and transform each of its query to apply to a related field instead

    Example:
        Q_for_related(Q(user_id=1), "project") -> will become -> Q(project__user_id=1)

    Works for complex Q object using composition of ~, & and | also,
    apply the same transformation to each sub element
    """
    new_q = Q()
    for sub_q in q.children:
        new_q.connector = q.connector
        new_q.negated = q.negated
        if isinstance(sub_q, Q):
            # recursion
            sub_q = Q_for_related(sub_q, related_field)
        else:
            # query transformation
            lookup_field, lookup_value = sub_q
            sub_q = (f"{related_field}__{lookup_field}", lookup_value)
        new_q.children.append(sub_q)
    return new_q
