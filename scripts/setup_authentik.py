"""Setup Authentik OAuth2 application for the Studio backend.

Uses Django management shell inside the Authentik container to create
the OAuth2 provider and application directly in the database.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]


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


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


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
    run(["npx", "wait-on", "http-get://localhost:9000/-/health/ready/"])


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


def set_akadmin_password() -> None:
    print("Setting akadmin password...")
    script = (
        "from authentik.core.models import User\n"
        "user = User.objects.get(username='akadmin')\n"
        "user.set_password('admin')\n"
        "user.save()\n"
        "print('Password set for akadmin')"
    )
    output = docker_ak_shell(script)
    for line in output.splitlines():
        if line.startswith("Password"):
            print(line)


def create_mcpuser() -> None:
    print("Creating second test user (mcpuser)...")
    script = (
        "from authentik.core.models import User\n"
        "user, created = User.objects.get_or_create(\n"
        "    username='mcpuser',\n"
        "    defaults={\n"
        "        'name': 'MCP Test User',\n"
        "        'email': 'mcpuser@localhost',\n"
        "    }\n"
        ")\n"
        "user.set_password('mcppass')\n"
        "user.save()\n"
        "action = 'Created' if created else 'Updated'\n"
        "print(f'{action} mcpuser')"
    )
    output = docker_ak_shell(script)
    for line in output.splitlines():
        if line.startswith(("Created", "Updated")):
            print(line)


def create_oauth2_provider(backend_url: str) -> None:
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

backend_url = '{backend_url}'
redirect_uris = [
    RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url=f'{{backend_url}}/auth/callback'),
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
        'meta_launch_url': f'{{backend_url}}/',
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
    import urllib.request

    url = "http://localhost:9000/application/o/studio/.well-known/openid-configuration"
    try:
        with urllib.request.urlopen(url) as resp:
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

    backend_url = os.environ.get(
        "BACKEND_BASE_URL",
        os.environ.get("VITE_BACKEND_BASE_URL", "http://localhost:10090"),
    ).rstrip("/")
    print(f"Using BACKEND_URL: {backend_url}")

    wait_for_authentik_health()
    wait_for_default_flows()
    set_akadmin_password()
    create_mcpuser()
    create_oauth2_provider(backend_url)
    verify_discovery()


if __name__ == "__main__":
    main()
