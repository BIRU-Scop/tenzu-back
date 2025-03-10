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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .exceptions import TokenBackendError, TokenError
from .settings import api_settings
from .token_blacklist.models import BlacklistedToken, OutstandingToken
from .utils import aware_utcnow, datetime_from_epoch, datetime_to_epoch, format_lazy


class Token:
    """
    A class which validates and wraps an existing JWT or can be used to build a
    new JWT.
    """

    token_type: Optional[str] = None
    lifetime: Optional[timedelta] = None

    def __init__(self, token: Optional[Any] = None, verify: bool = True) -> None:
        """
        !!!! IMPORTANT !!!! MUST raise a TokenError with a user-facing error
        message if the given token is invalid, expired, or otherwise not safe
        to use.
        """
        if self.token_type is None or self.lifetime is None:
            raise TokenError(_("Cannot create token with no type or lifetime"))

        self.token = token
        self.current_time = aware_utcnow()

        # Set up token
        if token is not None:
            # An encoded token was provided
            token_backend = self.get_token_backend()

            # Decode token
            try:
                self.payload = token_backend.decode(token, verify=verify)
            except TokenBackendError as e:
                raise TokenError(_("Token is invalid or expired")) from e

            if verify:
                self.verify()
        else:
            # New token.  Skip all the verification steps.
            self.payload = {api_settings.TOKEN_TYPE_CLAIM: self.token_type}

            # Set "exp" and "iat" claims with default value
            self.set_exp(from_time=self.current_time, lifetime=self.lifetime)
            self.set_iat(at_time=self.current_time)

            # Set "jti" claim
            self.set_jti()

    def __repr__(self):
        return repr(self.payload)

    def __getitem__(self, key: str):
        return self.payload[key]

    def __setitem__(self, key: str, value: Any):
        self.payload[key] = value

    def __delitem__(self, key: str):
        del self.payload[key]

    def __contains__(self, key: str):
        return key in self.payload

    def get(self, key: str, default=None):
        return self.payload.get(key, default)

    def __str__(self) -> str:
        """
        Signs and returns a token as a base64 encoded string.
        """
        return self.get_token_backend().encode(self.payload)

    def verify(self) -> Any:
        """
        Performs additional validation steps which were not performed when this
        token was decoded.  This method is part of the "public" API to indicate
        the intention that it may be overridden in subclasses.
        """
        # According to RFC 7519, the "exp" claim is OPTIONAL
        # (https://tools.ietf.org/html/rfc7519#section-4.1.4).  As a more
        # correct behavior for authorization tokens, we require an "exp"
        # claim.  We don't want any zombie tokens walking around.
        self.check_exp()

        # If the defaults are not None then we should enforce the
        # requirement of these settings.As above, the spec labels
        # these as optional.
        if (
            api_settings.JTI_CLAIM is not None
            and api_settings.JTI_CLAIM not in self.payload
        ):
            raise TokenError(_("Token has no id"))

        if api_settings.TOKEN_TYPE_CLAIM is not None:
            self.verify_token_type()

    def verify_token_type(self) -> Any:
        """
        Ensures that the token type claim is present and has the correct value.
        """
        try:
            token_type = self.payload[api_settings.TOKEN_TYPE_CLAIM]
        except KeyError as e:
            raise TokenError(_("Token has no type")) from e

        if self.token_type != token_type:
            raise TokenError(_("Token has wrong type"))

    def set_jti(self) -> None:
        """
        Populates the configured jti claim of a token with a string where there
        is a negligible probability that the same string will be chosen at a
        later time.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.7
        """
        self.payload[api_settings.JTI_CLAIM] = uuid4().hex

    def set_exp(
        self,
        claim: str = "exp",
        from_time: Optional[datetime] = None,
        lifetime: Optional[timedelta] = None,
    ) -> None:
        """
        Updates the expiration time of a token.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.4
        """
        if from_time is None:
            from_time = self.current_time

        if lifetime is None:
            lifetime = self.lifetime

        self.payload[claim] = datetime_to_epoch(from_time + lifetime)

    def set_iat(self, claim: str = "iat", at_time: Optional[datetime] = None) -> None:
        """
        Updates the time at which the token was issued.

        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.6
        """
        if at_time is None:
            at_time = self.current_time

        self.payload[claim] = datetime_to_epoch(at_time)

    def check_exp(self, claim: str = "exp", current_time: Optional[datetime] = None):
        """
        Checks whether a timestamp value in the given claim has passed (since
        the given datetime value in `current_time`).  Raises a TokenError with
        a user-facing error message if so.
        """
        if current_time is None:
            current_time = self.current_time

        try:
            claim_value = self.payload[claim]
        except KeyError as e:
            raise TokenError(format_lazy(_("Token has no '{}' claim"), claim)) from e

        claim_time = datetime_from_epoch(claim_value)
        leeway = self.get_token_backend().get_leeway()
        if claim_time <= current_time - leeway:
            raise TokenError(format_lazy(_("Token '{}' claim has expired"), claim))

    @classmethod
    def for_user(cls, user: AbstractBaseUser) -> "Token":
        """
        Returns an authorization token for the given user that will be provided
        after authenticating the user's credentials.
        """
        user_id = getattr(user, api_settings.USER_ID_FIELD)
        if not isinstance(user_id, int):
            user_id = str(user_id)

        token = cls()
        token[api_settings.USER_ID_CLAIM] = user_id

        return token

    _token_backend = None

    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = import_string("ninja_jwt.state.token_backend")
        return self._token_backend

    def get_token_backend(self):
        # Backward compatibility.
        return self.token_backend


class BlacklistMixin:
    """
    If the `ninja_jwt.token_blacklist` app was configured to be
    used, tokens created from `BlacklistMixin` subclasses will insert
    themselves into an outstanding token list and also check for their
    membership in a token blacklist.
    """

    if "ninja_jwt.token_blacklist" in settings.INSTALLED_APPS:

        def verify(self, *args, **kwargs):
            self.check_blacklist()

            super().verify(*args, **kwargs)

        def check_blacklist(self) -> None:
            """
            Checks if this token is present in the token blacklist.  Raises
            `TokenError` if so.
            """
            jti = self.payload[api_settings.JTI_CLAIM]

            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                raise TokenError(_("Token is blacklisted"))

        def blacklist(self) -> BlacklistedToken:
            """
            Ensures this token is included in the outstanding token list and
            adds it to the blacklist.
            """
            jti = self.payload[api_settings.JTI_CLAIM]
            exp = self.payload["exp"]

            # Ensure outstanding token exists with given jti
            token, _ = OutstandingToken.objects.get_or_create(
                jti=jti,
                defaults={
                    "token": str(self),
                    "expires_at": datetime_from_epoch(exp),
                },
            )

            return BlacklistedToken.objects.get_or_create(token=token)

        @classmethod
        def for_user(cls, user: "AbstractBaseUser") -> Token:
            """
            Adds this token to the outstanding token list.
            """
            token = super().for_user(user)

            jti = token[api_settings.JTI_CLAIM]
            exp = token["exp"]

            OutstandingToken.objects.create(
                user=user,
                jti=jti,
                token=str(token),
                created_at=token.current_time,
                expires_at=datetime_from_epoch(exp),
            )

            return token


class SlidingToken(BlacklistMixin, Token):
    token_type: str = "sliding"
    lifetime: timedelta = api_settings.SLIDING_TOKEN_LIFETIME

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.token is None:
            # Set sliding refresh expiration claim if new token
            self.set_exp(
                api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM,
                from_time=self.current_time,
                lifetime=api_settings.SLIDING_TOKEN_REFRESH_LIFETIME,
            )


class AccessToken(Token):
    token_type: str = "access"
    lifetime: timedelta = api_settings.ACCESS_TOKEN_LIFETIME


class RefreshToken(BlacklistMixin, Token):
    token_type: str = "refresh"
    lifetime: timedelta = api_settings.REFRESH_TOKEN_LIFETIME
    no_copy_claims: Tuple = (
        api_settings.TOKEN_TYPE_CLAIM,
        "exp",
        # Both of these claims are included even though they may be the same.
        # It seems possible that a third party token might have a custom or
        # namespaced JTI claim as well as a default "jti" claim.  In that case,
        # we wouldn't want to copy either one.
        api_settings.JTI_CLAIM,
        "jti",
    )
    access_token_class = AccessToken

    @property
    def access_token(self) -> "AccessToken":
        """
        Returns an access token created from this refresh token.  Copies all
        claims present in this refresh token to the new access token except
        those claims listed in the `no_copy_claims` attribute.
        """
        access = self.access_token_class()

        # Use instantiation time of refresh token as relative timestamp for
        # access token "exp" claim.  This ensures that both a refresh and
        # access token expire relative to the same time if they are created as
        # a pair.
        access.set_exp(from_time=self.current_time)

        no_copy = self.no_copy_claims
        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access


class UntypedToken(Token):
    token_type: str = "untyped"
    lifetime: timedelta = timedelta(seconds=0)

    def verify_token_type(self) -> None:
        """
        Untyped tokens do not verify the "token_type" claim.  This is useful
        when performing general validation of a token's signature and other
        properties which do not relate to the token's intended use.
        """
        pass
