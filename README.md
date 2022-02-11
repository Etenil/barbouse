# BARBOUSE

Postman for bearded API users.

Barbouse is an API exploration/testing utility that relies on a simple
file format and leverages existing operating-system mechanics.

## Quick start

Making a request is a simple as writing the following file, let's call it `request.txt`:

```
#GET^http://myapi.com/some/resource
```

Run with:

```
barbouse request.txt
```

## File format

The barbouse file format is as follows:

```
#METHOD^URL
#HEADER: HEADER_VALUE
#HEADER: HEADER_VALUE
#...
#|<JQ_FILTER>

PAYLOAD
```

Headers, the JQ filter and the payload are optional. The empty line above the
payload is significant and must be present.

Refer to the [JQ documentation](https://stedolan.github.io/jq/manual/) for filters.


## Running requests

Barbouse can run multiple request files given on the command line:

```
barbouse <file1> <file2>
```

## Command line arguments

The following arguments are supported:

- `-H, --headers` to only output headers
- `-b, --body` to only output the response body
- `-r, --raw` to disable body formatting (JSON only)
- `-f, --filter` to override the JQ filter for the request

