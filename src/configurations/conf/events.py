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

from enum import Enum
from typing import Dict

from pydantic_settings import BaseSettings


class PubSubBackendChoices(Enum):
    MEMORY = "channels.layers.InMemoryChannelLayer"
    REDIS = "channels_redis.pubsub.RedisPubSubChannelLayer"


class EventsSettings(BaseSettings):
    PUBSUB_BACKEND: PubSubBackendChoices = PubSubBackendChoices.REDIS

    # Settings for PubSubBackendChoices.MEMORY
    # -- none --

    # Settings for PubSubBackendChoices.REDIS
    REDIS_HOST: str = "tenzu-redis"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 0
    REDIS_OPTIONS: Dict[str, str|int] = {}