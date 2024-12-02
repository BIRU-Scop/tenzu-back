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

################################
# CONSTANTS
################################

# Projects
PROB_PROJECT_WITH_LOGO = 70  # 0-100

# Stories
STORY_TITLE_MAX_SIZE = (
    ((75,) * 3) + ((200,) * 6) + (400,)
)  # 75 chars (30%), 200 chars (60%), 400 chars (10%)
NUM_STORIES_PER_WORKFLOW = (0, 30)  # (min, max) by default
PROB_STORY_ASSIGNMENTS = {  # 0-99 prob of a story to be assigned by its workflow status
    "New": 10,
    "Ready": 40,
    "In Progress": 80,
    "Done": 95,
}
PROB_STORY_ASSIGNMENTS_DEFAULT = 25

# Story Comments
MAX_DAYS_LAST_COMMENT = 12  # referred to the creation date of the story they comment
MAX_STORY_COMMENTS = {  # Max number of comments (in the positive case of having comments)
    "New": 2,
    "Ready": 5,
    "In Progress": 10,
    "Done": 15,
}
MAX_STORY_COMMENTS_DEFAULT = 5
PROB_STORY_COMMENTS = {  # 0-99 prob of a story to be commented by its workflow status
    "New": 10,
    "Ready": 20,
    "In Progress": 40,
    "Done": 80,
}
PROB_STORY_COMMENTS_DEFAULT = 25
PROB_MODIFIED_COMMENT = 10  # 0-99 prob of a comment to be modified
PROB_DELETED_COMMENT = 10  # 0-99 prob of a comment to be deleted
