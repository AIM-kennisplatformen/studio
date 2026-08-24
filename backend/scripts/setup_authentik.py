"""Setup Authentik OAuth2 application for the Studio backend.

Uses Django management shell inside the Authentik container to create
the OAuth2 provider and application directly in the database.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

root = Path(__file__).resolve().parents[2]


def load_env(env_file_name: str = ".env") -> None:
    """Load environment variables from the given env file."""
    env_path = root / env_file_name
    if not env_path.exists():
        return
    print(f"Loading environment from: {env_path}")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)


def docker_ak_shell(script: str) -> str:
    """Run a Python script inside the Authentik container via `ak shell`."""
    result = subprocess.run(
        ["docker", "exec", "authentik-server", "ak", "shell", "-c", script],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def wait_for_authentik_health() -> None:
    print("Waiting for Authentik to be healthy...")
    health_url = f"{authentik_base_url()}/-/health/ready/"
    for attempt in range(1, 61):
        try:
            with urlopen(health_url, timeout=5) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        if attempt == 60:
            print(f"FAIL: Timed out waiting for {health_url}")
            sys.exit(1)
        time.sleep(2)


def authentik_base_url() -> str:
    configured = os.environ.get("AUTHENTIK_BASE_URL")
    if configured:
        return configured.rstrip("/")

    discovery_url = os.environ.get("OAUTH_DISCOVERY_URL")
    if discovery_url:
        parsed = urlsplit(discovery_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    return "http://localhost:10091"


def wait_for_default_flows() -> None:
    print("Waiting for Authentik default flows to be created...")
    script = (
        "from authentik.flows.models import Flow\n"
        "print(Flow.objects.filter(slug='default-provider-authorization-implicit-consent').exists())"
    )
    for i in range(1, 91):
        output = docker_ak_shell(script)
        if output.splitlines()[-1:] == ["True"]:
            print("OK: Default flows ready")
            return
        if i == 90:
            print("FAIL: Timed out waiting for default flows")
            sys.exit(1)
        time.sleep(2)


def create_oauth2_provider(frontend_url: str) -> None:
    print("Creating OAuth2 provider and application...")
    script = f"""\
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping, RedirectURI, RedirectURIMatchingMode
from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.crypto.builder import CertificateBuilder

auth_flow = Flow.objects.get(slug='default-provider-authorization-implicit-consent')

try:
    signing_key = CertificateKeyPair.objects.get(name='studio-signing-key')
    print(f'Using existing signing key: {{signing_key.name}}')
except CertificateKeyPair.DoesNotExist:
    builder = CertificateBuilder('studio-signing-key')
    builder.common_name = 'studio-signing-key'
    builder.build(subject_alt_names=[], validity_days=3650)
    signing_key = builder.save()
    print(f'Created signing key: {{signing_key.name}}')

scope_mappings = ScopeMapping.objects.filter(scope_name__in=['openid', 'email', 'profile'])

frontend_url = '{frontend_url}'
redirect_uris = [
    RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url='http://localhost:10090/auth/callback'),
    RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url='http://host.docker.internal:10090/auth/callback'),
]
seen = set()
unique_uris = []
for uri in redirect_uris:
    if uri.url not in seen:
        seen.add(uri.url)
        unique_uris.append(uri)
redirect_uris = unique_uris

provider, created = OAuth2Provider.objects.update_or_create(
    name='Studio OAuth2 Provider',
    defaults={{
        'authorization_flow': auth_flow,
        'client_type': 'confidential',
        'client_id': '9h9FmtG9XSqvm4zyUVqIzpV3q0p2EVG5MsGJPoa2',
        'client_secret': 'Wfx8Z7FAxFB9g5t7BJRmNTsOUYuXzXIIPc8KTNpkyv5jO34Ia4q3uSYmQwoMAgMpMpoOz5AO1qraJBfxLOy2zxskp7vXsLTlrzatLoECnDW6YmDBvjuwwM92QyUG09Db',
        'redirect_uris': redirect_uris,
        'sub_mode': 'hashed_user_id',
        'include_claims_in_id_token': True,
        'issuer_mode': 'per_provider',
        'signing_key': signing_key,
    }}
)
provider.property_mappings.set(scope_mappings)
provider.save()
action = 'Created' if created else 'Updated'
print(f'{{action}} OAuth2 provider (pk={{provider.pk}})')

app, created = Application.objects.update_or_create(
    slug='studio',
    defaults={{
        'name': 'Studio',
        'provider': provider,
        'meta_launch_url': f'{{frontend_url}}/',
    }}
)
action = 'Created' if created else 'Updated'
print(f'{{action}} application (slug={{app.slug}})')
"""
    output = docker_ak_shell(script)
    for line in output.splitlines():
        if line.startswith(("Created", "Updated", "Using", "Error", "Traceback")):
            print(line)


def verify_discovery() -> None:
    print("Verifying discovery endpoint...")
    url = f"{authentik_base_url()}/application/o/studio/.well-known/openid-configuration"
    try:
        with urlopen(url) as resp:
            if resp.status == 200:
                print("OK: OAuth2 application setup complete!")
            else:
                print(f"FAIL: Discovery endpoint returns {resp.status}")
                sys.exit(1)
    except Exception as exc:
        print(f"FAIL: Discovery endpoint error: {exc}")
        sys.exit(1)


def main() -> None:
    load_env(".env")

    frontend_url = os.environ.get(
        "FRONTEND_BASE_URL",
        "http://localhost:10090",
    ).rstrip("/")
    print(f"Using FRONTEND_URL: {frontend_url}")

    wait_for_authentik_health()
    wait_for_default_flows()
    create_oauth2_provider(frontend_url)
    verify_discovery()


if __name__ == "__main__":
    main()
