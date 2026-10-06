
import httpx
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer

KEYCLOAK_URL = "https://auth.sivaxi.com"
KEYCLOAK_REALM = "ai"
KEYCLOAK_CLIENT_ID = "sivaxi-ai"

KEYCLOAK_ISSUER = (
    f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
)

AUTHORIZATION_URL = (
    f"{KEYCLOAK_ISSUER}"
    "/protocol/openid-connect/auth"
)

TOKEN_URL = (
    f"{KEYCLOAK_ISSUER}"
    "/protocol/openid-connect/token"
)

JWKS_URL = (
    f"{KEYCLOAK_ISSUER}"
    "/protocol/openid-connect/certs"
)


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=AUTHORIZATION_URL,
    tokenUrl=TOKEN_URL,
    scopes={
        "openid": "OpenID",
        "profile": "User profile",
        "email": "User email",
    },
)


def get_jwks():
    response = httpx.get(
        JWKS_URL,
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def get_signing_key(token: str, jwks: dict):
    """
    Find the Keycloak public key matching the JWT kid.
    """

    header = jwt.get_unverified_header(token)

    kid = header.get("kid")

    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a key ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Signing key not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    try:
        # Fetch Keycloak public keys
        jwks = get_jwks()

        # Find the key that signed this JWT
        signing_key = get_signing_key(
            token,
            jwks,
        )

        # Validate and decode JWT
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={
                "verify_aud": False,
            },
        )

        print("\n========== KEYCLOAK TOKEN ==========")
        print("SUB:", payload.get("sub"))
        print("ISS:", payload.get("iss"))
        print("AZP:", payload.get("azp"))
        print("AUD:", payload.get("aud"))
        print("EXP:", payload.get("exp"))
        print("====================================\n")

        # Verify that the token was issued for our application
        if payload.get("azp") != KEYCLOAK_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token client",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except HTTPException:
        raise

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError as e:
        print("\n========== JWT ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("===============================\n")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except httpx.HTTPError as e:
        print("\n========== KEYCLOAK HTTP ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==========================================\n")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to reach authentication server",
        )

