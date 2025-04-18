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

from django.db.models.lookups import In

from base.db.models import SaveAsLowerCaseMixin

__all__ = ["CaseInsensitiveIn"]


@SaveAsLowerCaseMixin.register_lookup
class CaseInsensitiveIn(In):
    """
    Case-insensitive version of __in filter, for fields inheriting from SaveAsLowerCaseMixin
    """

    lookup_name = "iin"

    def process_rhs(self, compiler, connection):
        rhs, params = super().process_rhs(compiler, connection)
        return rhs, tuple(p.lower() for p in params)
