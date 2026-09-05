# Security and Privacy Requirements

## Security

- Store connector credentials in a managed secrets system.
- Apply least-privilege access to APIs, storage, queues, and databases.
- Enforce role-based access control (viewer, analyst, admin) at the API layer for raw evidence, risk detail, connector configuration, and exports — not only in the UI.
- Encrypt data in transit and at rest where appropriate.
- Isolate tenants if multi-tenancy is enabled.
- Audit administrative and data-access events.
- Rotate credentials and support connector revocation.
- Never place API keys or tokens in prompts, logs, source records, or Git history.

## Privacy

The platform should collect the minimum personal data necessary for its intelligence purpose. Public availability does not automatically mean unrestricted reuse.

Support:

- Configurable retention
- Deletion workflows
- Source-specific retention policies
- Pseudonymization where practical
- Access controls
- Regional storage policies where required
- Data-subject request workflows where applicable

## Sensitive content

The system should avoid unnecessarily collecting sensitive personal information and should provide configurable redaction for names, contact details, credentials, and other sensitive data when not needed for analysis.

## Compliance

Each connector must record applicable terms, license restrictions, data-use limits, geographic restrictions, and retention rules. The system must not bypass authentication, access controls, paywalls, private groups, or other restrictions.

## AI safety

Analyst outputs must distinguish discussion from fact. Allegations, rumors, satire, and unverified claims must be labeled appropriately. High-impact risk outputs should retain supporting evidence and confidence.

## Incident response

Security incidents, source-policy violations, credential exposure, and unexpected data leakage must have an auditable incident workflow, credential revocation path, and affected-data assessment.
