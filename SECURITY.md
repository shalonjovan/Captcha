# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.x | Yes |
| Earlier / unreleased forks | No |

## Reporting a vulnerability

Please **do not open a public issue** for a security vulnerability. Use GitHub's
private security advisory flow:

<https://github.com/shalonjovan/Captcha/security/advisories/new>

Include:

- a description of the issue and its impact;
- steps to reproduce, including a minimal script if possible;
- the affected version and Python/platform details;
- any suggested fix or mitigation.

You can expect an acknowledgement within a few business days. Please allow time
for a fix and coordinated disclosure before publishing details.

## Scope

Captcha Forge generates challenge images. The following are **not**
vulnerabilities in this library:

- a CAPTCHA being solvable by OCR or machine learning;
- a generated challenge being reused when the application does not expire it;
- an application returning `CaptchaResult.answer` to the client;
- missing server-side rate limiting or session controls in a consuming app;
- accessibility limitations inherent to a visual challenge.

The [security guide](docs/security.md) explains the responsibilities of the
integrating application. Reports about misleading documentation or unsafe
defaults are still welcome.

## Safe harbor

We support good-faith security research on the library itself. Do not test
against systems you do not own or have permission to test, and do not include
real user data in reports.
