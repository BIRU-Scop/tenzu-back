# Changelog

All notable changes to this project will be documented in this file. See [commit-and-tag-version](https://github.com/absolute-version/commit-and-tag-version) for commit guidelines.

## [0.0.1-staging.9](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.8...v0.0.1-staging.9) (2025-01-27)


### Features

* add landing_page field to more serializers ([a330b43](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/a330b4361addbcb856a4a1ccf419956f9f88f8b4))
* put some sequential db operation inside transaction ([421e1c2](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/421e1c24b9b2cd3d8972ff18027022e22ab55ef8))
* remove pyhumps dependency ([8a77a2f](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8a77a2f2aee24b211fdca279d150c8ab386ac7f5))
* update landing_page on rename workflow and add project event update ([dac0381](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/dac0381a777ecc48ab59fbefc53cc188c789b7f2))


### Bug Fixes

* add can authenticate check to create_auth_credentials ([4faa6a9](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/4faa6a9c214eb8609e9af6dd55525ae9b59ac488))
* fix workflow slug ([6e4b1b2](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6e4b1b28e2a1415b59500f282a01f7ed01c6f757))
* make async jwt tests pass ([82e70c1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/82e70c1b95e7df33d82fcee0ab1b9d0fa49e4fb7))
* prevent having two logo field in API definition ([97df03e](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/97df03e29d54baaf6c67bdc709f1696b2c3b567a))
* remove assert from validation, add guard for optional field and rename misleading mixin class ([66f9c35](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/66f9c3580abf40d1b9da0321c33c27c9daccb9c1))
* repair some constraint that were not validated ([bf37cf1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/bf37cf13757aff14a4291b91830efc991ba4c2a3))
* rollback camelize restriction ([9f8010a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9f8010a891559cf5d1cbbe39f0a5e268a7512a61))
* working projects tests and fix some validation check that were not run ([92f87ea](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/92f87ea6cede4948c14dcda419b94a35a331bbde))
* working stories tests and fix uncovered bugs ([07ccddc](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/07ccddcfcde8a55ff4cd0b2f190e0ce9bfd963b6))

## [0.0.1-staging.8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.7...v0.0.1-staging.8) (2025-01-13)


### Features

* add username or email authentication ([2e9806a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/2e9806a94b9e0157dbdcc4e2e3acd768c770ae99))
* refactor color usage and update all migrations ([5f71c29](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/5f71c296586f46f8e65369f153341489af8922c6))
* remove custom json encoder ([6ba5531](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6ba5531ac091c7e58c745396aa2dafdafd17ab9a))
* remove tokens app and standardise jwt ([d264c0b](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/d264c0bda44d6c8e7021187eb25f2b1b75ea1d19))
* **serializers:** add status_id to story serializers ([c27e971](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/c27e971663974c940419b901496d0f105ca0ff84))


### Bug Fixes

* delete project ([1fd0705](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1fd070520f052bc1fd1afbecf95a4d88583700ef))
* fix status id into the update input ([b62ea1b](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/b62ea1b3329a2964cdab888b6eddb034b967591e))
* invitation systems works with ninja_jwt tokens ([dab0463](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/dab046387421064e2b815c0a3732059626bdc73b))
* prevent validation error when serialising url with new media file and version config ([5a10c56](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/5a10c56f8f6a507f9e51e0b46ab67703aa84c1d5))

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
