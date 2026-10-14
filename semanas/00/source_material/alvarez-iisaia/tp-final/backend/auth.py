from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

from authlib.integrations.httpx_client import AsyncOAuth2Client

from backend.config import Settings


class AuthError(RuntimeError):
    """Error seguro y esperable durante el flujo OIDC."""


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
        async with AsyncOAuth2Client(
            client_id=self.settings.auth0_client_id,
            client_secret=self.settings.auth0_client_secret,
            redirect_uri=self.settings.auth0_callback_url,
            scope="openid profile email",
        ) as client:
            metadata_response = await client.get(metadata_url)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()
            token = await client.fetch_token(metadata["token_endpoint"], code=code)
            claims = await client.parse_id_token(
                token,
                nonce=nonce,
                claims_options={
                    "iss": {"essential": True, "value": metadata["issuer"]},
                    "aud": {
                        "essential": True,
                        "value": self.settings.auth0_client_id,
                    },
                },
            )
        sub = claims.get("sub")
        if not sub:
            raise AuthError("Auth0 no devolvió una identidad válida.")
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
