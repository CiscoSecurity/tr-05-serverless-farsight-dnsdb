[![Gitter Chat](https://img.shields.io/badge/gitter-join%20chat-brightgreen.svg)](https://gitter.im/CiscoSecurity/Threat-Response "Gitter Chat")

# NOTE! This code has been upgraded and the current release no longer supports installation in AWS
If you wish to deploy in AWS, use [this](https://github.com/CiscoSecurity/tr-05-serverless-farsight-dnsdb/releases/tag/v1.2.3) previous release.

# Farsight DNSDB Relay (Cisco Hosted)

Concrete Relay implementation using
[Farsight DNSDB](https://www.farsightsecurity.com/solutions/dnsdb/)
as a third-party Cyber Threat Intelligence service provider.

The Relay itself is just a simple application written in Python that can be
easily packaged and deployed. This relay is now Cisco Hosted and no longer requires AWS Lambda.

## Rationale

- We need an application that will translate API requests from SecureX Threat Response to the third-party integration, and vice versa. 
- We need an application that can be completely self contained within a virtualized container using Docker.  

## Testing (Optional)

Open the code folder in your terminal.
```
cd code
```

If you want to test the application you have to install a couple of extra
dependencies from the [test-requirements.txt](test-requirements.txt) file:
```
pip install --upgrade --requirement requirements.txt
```

You can perform two kinds of testing:

- Run static code analysis checking for any semantic discrepancies and
[PEP 8](https://www.python.org/dev/peps/pep-0008/) compliance:

  `flake8 .`

- Run the suite of unit tests and measure the code coverage:

  `coverage run --source api/ -m pytest --verbose tests/unit/ && coverage report`

If you want to test the live Lambda you may use any HTTP client (e.g. Postman),
just make sure to send requests to your Lambda's `URL` with the `Authorization`
header set to `Bearer <JWT>`.

**NOTE.** If you need input data for testing purposes you can use data from the
[observables.json](observables.json) file.

### Building the Docker Container
In order to build the application, we need to use a `Dockerfile`.  

 1. Open a terminal.  Build the container image using the `docker build` command.

```
docker build -t tr-05-farsight-dnsdb .
```

 2. Once the container is built, and an image is successfully created, start your container using the `docker run` command and specify the name of the image we have just created.  By default, the container will listen for HTTP requests using port 9090.

```
docker run -dp 9090:9090 --name tr-05-farsight-dnsdb tr-05-farsight-dnsdb
```

 3. Watch the container logs to ensure it starts correctly.

```
docker logs tr-05-farsight-dnsdb
```

 4. Once the container has started correctly, open your web browser to http://localhost:9090.  You should see a response from the container.

```
curl http://localhost:9090
```

## Implementation Details

### Implemented Relay Endpoints

- `POST /health`
  - Verifies the Authorization Bearer JWT and decodes it to restore the
  original credentials.
  - Authenticates to the underlying external service to check that the provided
  credentials are valid and the service is available at the moment.

- `POST /observe/observables`
  - Accepts a list of observables and filters out unsupported ones.
  - Verifies the Authorization Bearer JWT and decodes it to restore the
  original credentials.
  - Makes a series of requests to the underlying external service to query for
  some cyber threat intelligence data on each supported observable.
  - Maps the fetched data into appropriate CTIM entities.
  - Returns a list per each of the following CTIM entities (if any extracted):
    - `Sighting`.
    
- `POST /refer/observables`
  - Accepts a list of observables and filters out unsupported ones.
  - Builds a search link per each supported observable to pivot back to the
  underlying external service and look up the observable there.
  - Builds a browse link per each supported observable to pivot back
   directly to the observable page if there is one.
  - Returns a list of those links.

- `POST /version`
  - Returns the current version of the application.

### Supported Types of Observables

- `ip`
- `ipv6`
- `domain`

### CTIM Mapping Specifics

There are two possible mappings of Farsight `historical Domain->IP resolution` 
to CTIM `Sighting` which can be switched between with an environment variable `AGGREGATE`.

- If `Aggregated Mode` is off, each `resolution` generates a CTIM `Sighting`.
    - If an investigated observable is a `domain`, 
    it is linked to each `IP` item from the `resolution.rdata` field 
    with an observed relation `domain->'Resolved_To'->IP`. 
    - If an investigated observable is an `IP`, 
    it is linked to a `domain` from the `resolution.rrname` field
    with an observed relation `domain->'Resolved_To'->IP`.
    - The resolution `count` field is used as a `Sighting.count`.
    - Each Farsight `resolution` is timestamped with at least one pair of fields
    `time_first and time_last` (indicating the time an observable was seen via passive DNS replication)
    or `zone_time_first and zone_time_list` (indicating the time an observable was seen via zone file import)
    which is used as a `Sighting.observed_time`.
    The `Sighting.sensor` field depends on the time pair used and has a value 
    `Passive DNS replication` or `Zone file import` correspondingly. 
    If both pairs are presented, `time_first and time_last` pair is used.

- If `Aggregated Mode` is on, all `resolutions` for the last `90 days `
    generate a single CTIM `Sighting` 
    with unique values from the resolution `rdata` or `rrname` fields 
    linked as `Sighting` observed relations.
    - The sum of values from the resolution `count` is used as a `Sighting.count`.
    - The time of investigation is used as a `Sighting.observed_time.start_time`.

**NOTE.** If there are too many results, timeout or other performance issues may occur.
