from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

from authlib.jose import JoseError, jwt
import httpx

from backend.config import Settings


class AuthError(RuntimeError):
    """Error seguro y esperable durante el flujo OIDC."""

    def __init__(self, stage: str):
        super().__init__("No se pudo completar la autenticación.")
        self.stage = stage


@dataclass(frozen=True, slots=True)
class AuthIdentity:
    sub: str
    email: str | None
    name: str | None


class AuthProvider(Protocol):
    def authorization_url(
        self, *, state: str, nonce: str, screen_hint: str | None = None
    ) -> str: ...

    async def exchange_code(self, *, code: str, nonce: str) -> AuthIdentity: ...

    def logout_url(self) -> str: ...


class Auth0Provider:
    """Adaptador real. No realiza red hasta que se procesa un callback."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _require_configuration(self) -> None:
        self.settings.validated(require_auth0=True)

    def authorization_url(
        self, *, state: str, nonce: str, screen_hint: str | None = None
    ) -> str:
        self._require_configuration()
        params = {
            "response_type": "code",
            "client_id": self.settings.auth0_client_id,
            "redirect_uri": self.settings.auth0_callback_url,
            "scope": "openid profile email",
            "state": state,
            "nonce": nonce,
        }
        if screen_hint:
            params["screen_hint"] = screen_hint
        return f"https://{self.settings.auth0_domain}/authorize?{urlencode(params)}"

    async def exchange_code(self, *, code: str, nonce: str) -> AuthIdentity:
        self._require_configuration()
        metadata_url = f"https://{self.settings.auth0_domain}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            try:
                metadata_response = await client.get(metadata_url)
                metadata_response.raise_for_status()
                metadata = metadata_response.json()
            except (httpx.HTTPError, KeyError, ValueError) as error:
                raise AuthError("metadata") from error
            try:
                token_response = await client.post(
                    metadata["token_endpoint"],
                    data={
                        "grant_type": "authorization_code",
                        "client_id": self.settings.auth0_client_id,
                        "client_secret": self.settings.auth0_client_secret,
                        "code": code,
                        "redirect_uri": self.settings.auth0_callback_url,
                    },
                    headers={"Accept": "application/json"},
                )
                token_response.raise_for_status()
                token = token_response.json()
            except (httpx.HTTPError, KeyError, ValueError) as error:
                raise AuthError("token") from error
            try:
                jwks_response = await client.get(metadata["jwks_uri"])
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
            except (httpx.HTTPError, KeyError, ValueError) as error:
                raise AuthError("jwks") from error
            try:
                claims = jwt.decode(
                    token["id_token"],
                    jwks,
                    claims_options={
                        "iss": {"essential": True, "value": metadata["issuer"]},
                        "aud": {
                            "essential": True,
                            "value": self.settings.auth0_client_id,
                        },
                        "nonce": {"essential": True, "value": nonce},
                    },
                )
                claims.validate()
            except (JoseError, KeyError) as error:
                raise AuthError("claims") from error
        sub = claims.get("sub")
        if not sub:
            raise AuthError("identity")
        return AuthIdentity(sub=sub, email=claims.get("email"), name=claims.get("name"))

    def logout_url(self) -> str:
        self._require_configuration()
        query = urlencode(
            {
                "client_id": self.settings.auth0_client_id,
                "returnTo": self.settings.auth0_logout_return_url,
            }
        )
        return f"https://{self.settings.auth0_domain}/v2/logout?{query}"
