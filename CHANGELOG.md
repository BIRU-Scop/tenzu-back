# Changelog

All notable changes to this project will be documented in this file. See [commit-and-tag-version](https://github.com/absolute-version/commit-and-tag-version) for commit guidelines.

## [0.0.1-staging.7](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.6...v0.0.1-staging.7) (2024-12-02)


### Features

* Add workspace_id to project serializer ([54e1627](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/54e162765ed7c7f05a5c716889f4da5df9390caf))
* **api:** add inline viewing option for attachments ([76b8a09](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/76b8a0927146a4263d304e989c90529527c08d3f))
* **settings:** enable database connection pooling ([c4bab81](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/c4bab81b6889869732b015b2d5d29def6f206631))


### Bug Fixes

* **settings:** remove pool configuration for the database ([1fa2830](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1fa2830bbd3f7595a259f7943fef35ecba02a4d1))

## [0.0.1-staging.6](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.5...v0.0.1-staging.6) (2024-11-27)


### Bug Fixes

* prevent crash when displaying time with timedelta instead of minutes ([1509779](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1509779d292f8ec700276c9107a7b09f0b6cee02))

## [0.0.1-staging.5](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.4...v0.0.1-staging.5) (2024-11-26)


### Bug Fixes

* asgi conf wasn't loaded properly ([a60c413](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/a60c4139c0dc0fe9da587ab7762e7049467366d9))

## [0.0.1-staging.4](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.3...v0.0.1-staging.4) (2024-11-26)

## [0.0.1-staging.3](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.2...v0.0.1-staging.3) (2024-11-26)


### Features

* add project_id and workflow_id to all Story Serializer ([5b10315](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/5b103155734194aee785705ea1030d8698bbaddc))
* add websocket support for event and action ([ca10f37](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/ca10f37dcb8eab2f429cff31e933e429783ca684))
* add WorkspaceId to ProjectSerializer for notification ([8833898](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/88338980ce19cfbf17f660684ac8d62b0eda0ea8))
* restrain allowed host and refactor url usage ([0402e53](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/0402e53917d93e71be43145cd3d4e877fcb3ca8b))
* use argon2 for passwords ([05aded1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/05aded131208bb6135557f3c2f9d8be1f754ded6))


### Bug Fixes

* add correlation-id to cors allowed headers ([9bd6c8d](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9bd6c8decf8a7201c7caf8a5117c373202db2ba8))
* make static serving work by not using concurrent mount path ([2e2bac9](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/2e2bac9357b5b2a7704b1d1a7e50c59cd8f64ac5))
* rename event type for StoryAttachment to match the other event ([ee0dfe8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/ee0dfe81da2d6b651df70a2841a4a74fa014e500))
* repair settings usage for pydantic v2, remove default for secret keys and use timedelta directly ([19b21c1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/19b21c1f2b75cfd253890f87e71dea42810a7557))

## [0.0.1-staging.2](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.1...v0.0.1-staging.2) (2024-10-31)


### Bug Fixes

* redis default username ([7d8f561](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/7d8f561158d6032c62a1e0322f9b11485d07e3f9))

## [0.0.1-staging.1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.0...v0.0.1-staging.1) (2024-10-31)


### Bug Fixes

* add optional the notification system if redis is down ([764d74b](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/764d74b3e2be1e56c7d6ff92aa977ea80b8ebc34))

## 0.0.1-staging.0 (2024-10-29)
