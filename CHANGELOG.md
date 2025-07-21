# Changelog

All notable changes to this project will be documented in this file. See [commit-and-tag-version](https://github.com/absolute-version/commit-and-tag-version) for commit guidelines.

## [0.0.1-staging.28](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.27...v0.0.1-staging.28) (2025-07-21)

## [0.0.1-staging.27](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.26...v0.0.1-staging.27) (2025-07-18)

## [0.0.1-staging.26](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.25...v0.0.1-staging.26) (2025-07-17)


### Features

* add build setup to add extra dependencies to the project and handle licence year dynamically ([a95bf35](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/a95bf354b71285252b81b85c2f8d37980df8f316))
* compatibility with s3 for stat command and prevent file overwrite by default ([0a1ff29](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/0a1ff29362d56047862afc057623889afa22f788))
* handle http 424 ([43c3396](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/43c3396c96d92bac5f73c701aa709968edbd0222))
* make extra dependency more configurable and add whitenoise in dev environment ([9909c2d](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9909c2d90c8b48e47c7bf68d941000dc5ec527ff))
* remove mediafiles module ([08dd382](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/08dd382998da13ecebbc3bb7f7f3c1f6ba04945c))
* standardise repository for comments and attachement by removing all apply functions ([38b9015](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/38b9015f557e987787c5d02c4813e0e1dae23987))
* update example stories description data to use the format of blocknotejs ([7e46830](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/7e468309f363c0ac5e9b9491ee9f7218193fe7c2))

## [0.0.1-staging.25](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.24...v0.0.1-staging.25) (2025-06-24)


### Features

* add s3-storage ([566d6cd](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/566d6cdf40758f9d529fb2eb6173ffbba7d87b1a))
* remove mediafile endpoint ([e0909f0](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/e0909f018c7bd350dadbb89ef8b2eadc11336e0f))


### Bug Fixes

* make all file operations works with s3 storage ([912dd6c](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/912dd6c4037efc00003839b97b8ad91fa31ab4fe))
* prevent error when creating invitation for non-users only ([9f8a1d4](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9f8a1d4dbd80a18931f7cefcf27b1e264dfa8c0c))

## [0.0.1-staging.24](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.23...v0.0.1-staging.24) (2025-06-19)


### Bug Fixes

* prevent hash direct matching ([128e817](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/128e8175d8a6ad414cf8ed13673966611808828c))

## [0.0.1-staging.23](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.22...v0.0.1-staging.23) (2025-06-17)

## [0.0.1-staging.22](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.21...v0.0.1-staging.22) (2025-06-16)


### Bug Fixes

* temporary fix of performance ([382bd4e](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/382bd4e5bfd4e7353bd78706ec550a5cff18ab25))

## [0.0.1-staging.21](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.20...v0.0.1-staging.21) (2025-06-16)


### Features

* realtime invitation changes ([8383ceb](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8383cebeaa7e39a92e26807f757479fc33ec1c98))
* realtime invitation creation ([f854317](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/f854317eeb407659fd9b41d1029ac0d76888d0fc))
* realtime membership deletion ([8c80a1b](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8c80a1b16f3514737269a3e1967e1bf4cd79882f))
* realtime membership update ([9e74151](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9e74151fef307aef926072c5500f6fb1e77f429b))
* realtime project creation ([ef4599f](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/ef4599fc795a47dd7dc14c339d4d48552521ede3))
* realtime roles ([2ac978d](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/2ac978d683345310b4809127f91d06d6a5d1c08b))
* realtime workspace creation ([99da657](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/99da6570806bfddb88aff13140d807a0ac323870))
* realtime workspace update ([56689a4](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/56689a459281017d5cb7c30b4a4a8cf9c2600403))


### Bug Fixes

* serialise all modified invitation on bulk create, not just sent ones ([f837505](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/f837505d05ca5f45dc79aba1ff6ecdcaa0a0f9b8))

## [0.0.1-staging.20](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.19...v0.0.1-staging.20) (2025-06-13)

## [0.0.1-staging.19](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.18...v0.0.1-staging.19) (2025-06-12)


### Features

* switch back to workflow instead of status filter when listing stories ([03df407](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/03df40791cf6b5e99b9b63e23303236e88fa84ea))

## [0.0.1-staging.18](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.17...v0.0.1-staging.18) (2025-06-12)


### Features

* add has_invitees field to serialised role ([c7dcaff](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/c7dcaff412f02278b79aa0cf9aa8edef9f500601))
* add id field to serialized memberships ([45db728](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/45db7287f84770f9f6ed5f3cdcd9f322c12f079f))
* add more info to workspace list endpoint ([4fcfcb6](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/4fcfcb6dcb92fef21841844074e8c406befcf889))
* add possibility to name a successor when deleting a project membership ([61a654f](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/61a654fa4f00d6a580de6a6c9229338a3a72e9f6))
* add possibility to name a successor when deleting a workspace membership, also delete nested project memberships and handle edge cases ([28d526f](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/28d526f680a52e0030df0ce78545951f69568aa9))
* add webservice api endpoint to retrieve info useful before deleting a workspace membership ([a92402d](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/a92402ded02d64cced0a9cbf7f9608ff0887aee1))
* list story api endpoint now use status id as parameter instead of workflow ([e7297ee](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/e7297eeca48c558c5ca1e6b1f63aa4aa90d631de))
* **membership:** add number of project where user in member in workspace membership serializer ([6d87678](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6d876783cb0c1f702c4e2f6a544fac1cca79b05c))
* standardise stories api by using workflow id instead of slug ([1a83621](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1a83621f1960ba94521f4158c401e0072b747b15))
* switch project update back to being a patch request ([c16c7ff](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/c16c7ffcf8be78f949be616ecdbbf8b9f8f03ff6))


### Bug Fixes

* prevent crash on object deletion because of missing id when serialising events ([50c277a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/50c277af257fe36f26f3d576932c710ba766b016))
* prevent random ordering after using an annotate with implicite groupby ([e43ca7a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/e43ca7aeb72d5850dc37b8b90a6780008e028749))
* prevent successor from being same user as to-be-deleted member ([3774412](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/3774412ead8ba2a3b5ef307e0849ad63d2604f28))
* prevent validation error when deleting a role without a successor ([787bf4c](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/787bf4c843cb8406a65f627061d2fff4a6aaec68))

## [0.0.1-staging.17](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.16...v0.0.1-staging.17) (2025-05-29)


### Bug Fixes

* catch all possible permission error when checking user channel subscription permission ([897ca29](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/897ca2965416dd1c2ada6b17a3292aaa09b5e0d9))
* prevent crash on accepting project invitation when trying to acces unprefetched workspace ([6f649b3](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6f649b3be45b421c30036e1992c6e70a2bbf8c8c))

## [0.0.1-staging.16](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.15...v0.0.1-staging.16) (2025-05-28)


### Features

* add date fields in invitation serializer and return pending invitation first in list api ([eaee543](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/eaee5433bef23ccd1e49195cf4583c42d2bfd36b))
* add email field to user nested ([7d7e5f3](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/7d7e5f3828ad2202603fc641806973d4226536ec))
* add get role and total_number ([b0158ef](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/b0158efb17b47912d5024f9eab6d374e7660f673))
* remove nested stories from delete workflow event ([8b7a673](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8b7a673a5ef346978b3cf04e22a4788e4f90b949))
* standardise all apis to follow new rules about avoiding unnecessary url parameters and keeping dependant objects in path ([8868303](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/88683033a7b914db5ec6be6d061245a9aad6bc7c))
* standardise api by using object id instead of related user username ([1bfd319](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1bfd319a9803ac32dcb28f190d8ad522561865d1))
* standardise apis by using role_id instead of role_slug in forms ([1803ceb](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/1803ceba4f7540983dbb5e7776c26ba366ce9138))
* switch from role slug to role ID for project role API operations and add total_members field ([acbdd2f](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/acbdd2fba87651fd922ff9d900b19ddf68bf5eba))
* upscale default resend limit for invitation and serialise num_email_sent ([6019f85](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6019f85c9ccd647cfeb8104966534fb277d939e3))


### Bug Fixes

* make language api returns camelCase and refactor language service ([8d6fd95](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8d6fd95115a7126be15de886aa737e4221957c1c))
* prevent crash on incoherent existing invitation ([15d7e00](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/15d7e0016b77699760643d00bcb51e051e5aca51))
* prevent error on resend because workspace had not been prefetched for project invitation ([9172c51](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9172c51192ca5a01bb400b9229890231ff5bca6a))

## [0.0.1-staging.15](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.14...v0.0.1-staging.15) (2025-05-02)


### Bug Fixes

* make migration check happy with explicit through_fields ([10d6b1c](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/10d6b1cc6cc210c1d36143390d6050cbab72f933))

## [0.0.1-staging.14](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.13...v0.0.1-staging.14) (2025-04-28)


### Features

* absolute path for public folders instead of relatives ([71ac9e9](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/71ac9e9b0599e9ce2df437168213eefb4804a29b))
* add project role name edition to update role endpoint ([50fdebf](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/50fdebf02d9c14fc8dfdbb30092a4975f4c7618b))
* add total_project field to workspace detail ([00c9099](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/00c9099de7bbe1e2340532290e4ecece80d5c716))
* create project role api ([f9a91d8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/f9a91d895b7b26fcf902826f0369e759978d634c))
* delete project role api ([b1ce025](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/b1ce025b1f84c5906917a810fa15eaf4ceec3e6b))
* in workflow, rename status fields that actually only contains id to an explicit name ([b353a32](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/b353a3270465935b65480b7fb0bfe74dae145596))
* **invitations:** deny project invitation ([eccb418](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/eccb418ac9bc01207a5efac3a851d8627c291eaa))
* make list project returns invited and member project in one list with a differentiating attribute ([0cdbcc7](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/0cdbcc77cc79536830c097e836fdd1b5ce8ab295))
* make public invitation only returns pending ones and refactor some serializer classes ([3b859cf](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/3b859cf9d7ae029f0bece15b35bb45c45daec30f))
* make workspace and project invitation follow frontend constraints ([d3556b1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/d3556b186bbd0300c7853110c00f7722b8ed968d))
* remove unneeded guest event now that invited user can read workspace channel and add needed select_related ([bda08a5](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/bda08a5127537c17f6359a2ddca3e27c16de932c))
* some more info from project's invitation endpoints and add apis for workspace's update invitation membership role, accept by workspace, deny, revoke and resend ([0f45dd7](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/0f45dd7ee0879a109fa55aad7b9bb1287aae8b84))
* standardise project creation url path ([112c9d8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/112c9d8405c207c55e5e23f84905bdadccd8bc7e))
* standardise story url path and only accept number story ref in path resolution ([d59cbb6](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/d59cbb6c86ba66ec1ec8ff6edea47bd7d8f8254b))
* standardise workflow url to use id without needing project ([6edf27a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/6edf27ac8468021fcdee74929eedcba946d38c93))
* switch all order fields to int and handle edge case when reorder space is not enough ([8734490](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8734490b46f05255e8488715c3aef717282f0962))


### Bug Fixes

* add assignees in list view ([a77723a](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/a77723aa3cc96c313545522f630ef20ae22f5edf))
* prevent changing slug on each update even when name has not changed ([ededbd8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/ededbd87b6d6fadf67b0f55eef32814c1c1e4cfb))
* prevent pydantic warning about email folder path type ([50a7606](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/50a7606142b5158f0455e399679b874a8ca9e3ef))

## [0.0.1-staging.13](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.12...v0.0.1-staging.13) (2025-02-27)


### Bug Fixes

* make in-memory channel possible and add config to pass additional variable to redis-channel ([bab2788](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/bab278838e1048c00a6551af4bc8ba59df0ba6a8))
* use correct EMAIL_USE_LOCALTIME variable name and make overriding EMAIL_FILE_PATH easier ([fd7c513](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/fd7c5134528af67fc835f48b1a369ec6c170708a))

## [0.0.1-staging.12](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.11...v0.0.1-staging.12) (2025-02-08)


### Bug Fixes

* exclude fictive account from stats ([030cfdd](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/030cfddeca66eca56d9a83e487b58982ee4a4c1a))

## [0.0.1-staging.11](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.10...v0.0.1-staging.11) (2025-02-04)


### Features

* add flush_expired_tokens task ([4134dda](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/4134dda1b817a759ae48b19f7dbb02b0b66be078))
* command to export statistics about registration ([4bb9227](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/4bb92273cde71f20d52add0e11faf31d47160051))


### Bug Fixes

* ci mirroring ([84d8404](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/84d8404d367cba53fc1dd4ee9dfca80a0df59d6c))
* let django handle attachment file headers,now it works the same on all browsers for view and download ([760dea8](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/760dea8aff5cd37fb38f5a474eceabed4de4da26))
* put delete user inside transaction ([8fbbd3e](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/8fbbd3e31b354e27717571c06109f293c0f74929))
* remove filter on token_type ([ab53bf1](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/ab53bf1400f8a3b428cd7d9b62a1a367d491e2d0))
* reset password works with ninja_jwt tokens ([9e28fc6](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/9e28fc6d1a504a90d678a8d3fdb4f74b159404d3))

## [0.0.1-staging.10](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/compare/v0.0.1-staging.9...v0.0.1-staging.10) (2025-01-27)


### Bug Fixes

* prevent non-encoded serialisation of id in invitation ([0cb912c](https://gitlab.biru.sh/biru/dev/tenzu/tenzu-back/commit/0cb912cb5dcdda1ab7d009b010926282c33fb022))

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
