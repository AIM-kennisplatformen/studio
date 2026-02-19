#!/bin/bash
# Setup Authentik OAuth2 application for the Studio backend
# Uses Django management shell inside the Authentik container to create
# the OAuth2 provider and application directly in the database.

set -e

echo "Waiting for Authentik to be healthy..."
npx wait-on http-get://localhost:9000/-/health/ready/

echo "Waiting for Authentik default flows to be created..."
for i in $(seq 1 90); do
  FLOW_EXISTS=$(docker exec authentik-server ak shell -c "
from authentik.flows.models import Flow
print(Flow.objects.filter(slug='default-provider-authorization-implicit-consent').exists())
" 2>/dev/null | tail -1)
  if [ "$FLOW_EXISTS" = "True" ]; then
    echo "OK: Default flows ready"
    break
  fi
  if [ "$i" = "90" ]; then
    echo "FAIL: Timed out waiting for default flows"
    exit 1
  fi
  sleep 2
done

echo "Setting akadmin password..."
docker exec authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='akadmin')
user.set_password('admin')
user.save()
print('Password set for akadmin')
" 2>&1 | grep -E "^Password" || true

echo "Creating OAuth2 provider and application..."
docker exec authentik-server ak shell -c "
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping, RedirectURI, RedirectURIMatchingMode
from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.crypto.builder import CertificateBuilder

# Get the authorization flow
auth_flow = Flow.objects.get(slug='default-provider-authorization-implicit-consent')

# Get or create a signing key for JWT tokens
try:
    signing_key = CertificateKeyPair.objects.get(name='studio-signing-key')
    print(f'Using existing signing key: {signing_key.name}')
except CertificateKeyPair.DoesNotExist:
    builder = CertificateBuilder('studio-signing-key')
    builder.common_name = 'studio-signing-key'
    builder.build(subject_alt_names=[], validity_days=3650)
    signing_key = builder.save()
    print(f'Created signing key: {signing_key.name}')

# Get scope mappings
scope_mappings = ScopeMapping.objects.filter(scope_name__in=['openid', 'email', 'profile'])

# Build redirect URIs as dataclass instances
redirect_uris = [
    RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url='http://localhost:10090/auth/callback'),
    RedirectURI(matching_mode=RedirectURIMatchingMode.STRICT, url='http://host.docker.internal:10090/auth/callback'),
]

# Create or update the OAuth2 provider
provider, created = OAuth2Provider.objects.update_or_create(
    name='Studio OAuth2 Provider',
    defaults={
        'authorization_flow': auth_flow,
        'client_type': 'confidential',
        'client_id': '9h9FmtG9XSqvm4zyUVqIzpV3q0p2EVG5MsGJPoa2',
        'client_secret': 'Wfx8Z7FAxFB9g5t7BJRmNTsOUYuXzXIIPc8KTNpkyv5jO34Ia4q3uSYmQwoMAgMpMpoOz5AO1qraJBfxLOy2zxskp7vXsLTlrzatLoECnDW6YmDBvjuwwM92QyUG09Db',
        'redirect_uris': redirect_uris,
        'sub_mode': 'hashed_user_id',
        'include_claims_in_id_token': True,
        'issuer_mode': 'per_provider',
        'signing_key': signing_key,
    }
)
provider.property_mappings.set(scope_mappings)
provider.save()
action = 'Created' if created else 'Updated'
print(f'{action} OAuth2 provider (pk={provider.pk})')

# Create or update the application
app, created = Application.objects.update_or_create(
    slug='studio',
    defaults={
        'name': 'Studio',
        'provider': provider,
        'meta_launch_url': 'http://localhost:10090/',
    }
)
action = 'Created' if created else 'Updated'
print(f'{action} application (slug={app.slug})')
" 2>&1 | grep -E "^(Created|Updated|Using|Error|Traceback)" || true

# Verify
echo "Verifying discovery endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9000/application/o/studio/.well-known/openid-configuration")
if [ "$HTTP_CODE" = "200" ]; then
  echo "OK: OAuth2 application setup complete!"
else
  echo "FAIL: Discovery endpoint returns $HTTP_CODE"
  exit 1
fi
