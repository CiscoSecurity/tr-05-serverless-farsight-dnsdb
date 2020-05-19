[![Travis CI Build Status](https://api.travis-ci.com/CiscoSecurity/tr-05-serverless-farsight-dnsdb.svg?branch=develop)](https://api.travis-ci.com/CiscoSecurity/tr-05-serverless-farsight-dnsdb)

# Farsight DNSDB Relay API

The API is just a simple Flask (WSGI) application which can be easily
packaged and deployed as an AWS Lambda Function working behind an AWS API
Gateway proxy using [Zappa](https://github.com/Miserlou/Zappa).

An already deployed Relay API (e.g., packaged as an AWS Lambda Function) can
be pushed to Threat Response as a Relay Module using the
[Threat Response Relay CLI](https://github.com/threatgrid/tr-lambda-relay).

## Details

Farsight DNSDB Relay API implements the following endpoints:
- `/observe/observables`
- `/health`

Other endpoints (`/deliberate/observables`, `/refer/observables`,
 `/respond/observables`, `/respond/trigger`) returns empty responses.

Supported types of observables:
- `ip`
- `ipv6`
- `domain`

Other types of observables are ignored.

## Authorization

To query Farsight DNSDB API, API key is used:

```json
{
   "key": "<Farsight_DNSDB_API_KEY>"
}
```

Credentials must be encrypted with JWT.
After encryption set your `SECRET_KEY` environment 
variable in AWS lambda for successful decryption in Relay API.

## Installation

```bash
pip install -U -r requirements.txt
```

## Testing

```bash
pip install -U -r test-requirements.txt
```

- Check for *PEP 8* compliance: `flake8 .`.
- Run the suite of unit tests: `pytest -v tests/unit/`.

## Deployment

```bash
pip install -U -r deploy-requirements.txt
```

#### As an AWS Lambda Function:
- Deploy: `zappa deploy dev`.
- Check: `zappa status dev`.
- Update: `zappa update dev`.
- Monitor: `zappa tail dev --http`.

Environment Variables:

- `SECRET_KEY` - string key used while `JWT` encoding. Mandatory variable.
  
- `CTR_ENTITIES_LIMIT` - the maximum number of entities in a response.
 Applicable to: `Sighting`.
 Must be an integer, greater than zero.
 Default value - `100`, used if the variable is not set or set variable is incorrect.
 Has the upper bound of `1000` to avoid getting overwhelmed with too much data,
  so any greater values are still acceptable but also limited at the same time.

#### As a TR Relay Module:
- Create: `relay add`.
- Update: `relay edit`.
- Delete: `relay remove`.

**Note.** For convenience, each TR Relay CLI command may be prefixed with
`env $(cat .env | xargs)` to automatically read the required environment
variables from a `.env` file (i.e.`TR_API_CLIENT_ID`, `TR_API_CLIENT_PASSWORD`,
`URL`, `JWT`) and pass them to the corresponding command.

## Usage

```bash
pip install -U -r use-requirements.txt
```

```bash
export URL=<...>
export JWT=<...>

http POST "${URL}"/health Authorization:"Bearer ${JWT}"
http POST "${URL}"/observe/observables Authorization:"Bearer ${JWT}" < observables.json
```
