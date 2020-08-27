# lazyConfig

> lazily loading and overriding configuration for the lazy coder

lazyConfig is an opinionated configuration provider. Loading `.yml`, `.yaml`
or `.json` configuration files. Opinionated since it requires you to
structure your configuration in a certain way in order to work.

## Why lazyConfig?

see [Motivation](https://github.com/FelixBenning/lazyConfig/blob/master/Motivation.md)

## Usage

In order to load your configuration folder into a `dict` like structure, simply
point `lazyConfig` to the folder

```python
from lazyConfig import Config

config = Config.from_path(
    config='/path/to/default/config',
    '/path/to/override',
    '/path/to/another/override/',
    ...
)

# or with environment variables:

config = Config.from_env(config='DEFAULT_CONFIG_ENV_VAR', 'OVERRIDE1', ...)
```

where the environment variables should contain the path to the configuration
directories. Files are overriden left to right (i.e. the last argument has
priority)

> you can mix and match using `Config.from_path` and `os.environ[ENV_VAR]`

### Assumptions about the file structure

Since filenames are used as keys in the `config` dict, without any caveats
you would be forced to have a minimum depth of `1` for any configuration.

This might not make sense for some high level, flat configuration. For this
reason there is a special filename `__config__` (`.yml`,`.yaml` or `.json`),
which allows you to define top level keys and values.

### Example

```text
config
    database
        configuration.yml
        __config__.yml
    app.yml
    __config__.yml
```

`config/__config__.yml`:

```yml
name: my-app
author: ME!
version: -1.0
```

`app.yml`:

```yml
primary_color: 'blue'
secondary_color: 'green'
```

`config/database/__config__.yml`:

```yml
connection:
    hosts:
        - {host: "myElasticsearchServer", port: 9200}
    timeout: 6000
```

`config/database/configuration.yml`:

```yml
indices:
    index1: {...}
    index2: {...}
pipelines:
    pipeline1: {...}
```

would be loaded as the following dictionary (formatted in `yml` for readability):

```yml
name: my-app
author: ME!
version: -1.0
app:
    primary_color: 'blue'
    secondary_color: 'green'
database:
    connection:
        hosts:
            - {host: "myElasticsearchServer", port: 9200}
        timeout: 6000
    configuration:
        indices:
            index1: {...}
            index2: {...}
        pipelines:
            pipeline1: {...}
```

So you could access `index1` with:

```python
config.database.configuration.indices.index1
```

### Duplicate Keys

Duplicate Keys are not allowed. `lazyConfig` tries to find keys in

1. Keyfiles (`__config__`)
2. Filenames
3. Directories

*in that order*! It will not keep looking whether or not there is a duplicate and
thus ignore a directory if a file with the same name (sans extension) or a key
with the same name in the keyfile exists.

> There might be a configuration validation function in the future to check for
duplicate keys (in debug mode or on manual call)

### Attribute access

Python does not allow attributes to start with a number. So

```python
config.1attribute2breakthings
```

will not work. In these cases you will have to use

```python
config['1attribute2breakthings']
```

### Lists

Lists are overriden not extended. If the default configuration has the same key
for a list as an override, then the default list is ignored and the override is
used.

> Extending Lists would mean that you can not remove elements with a
configuration override. As this is not desirable you will just have to
duplicate lists in its entirety if you want to
change them (even if only slightly)

Since numbers are discouraged anyway, you can define **Directory Lists** like this:

```text
config
    list
        0.yml
        1.yml
        2.yml
        3.yml
```

which is then converted to

```yml
config:
    list:
        - {content from 0.yml}
        - {content from 1.yml}
        - {content from 2.yml}
```

Directory Lists **must** start with `0` and end with `n-1` where `n` is the
number of files in the directory.
> It is currently not possible to create a list of directories (instead of files).
This might become a feature in a future version if requested

## Security

Using `pyYAML.unsafe_load()`, `lazyConfig` is currently not meant for external data.

## Future Features

things which I might get around to do some time:

- other configuration languages/parsers (e.g. TOML, safe config loaders, etc.)
- Configuration Validation
- Horizontal override (Templates, e.g. for indices)
- Configuration Setter
    > Since it is not obvious where to set directory/file boundaries inside the
    dictionary, this is not as trivial as it might seem at first. It might be
    necessary to provide the grouping level as an argument.
- generate [JSON Schema](https://json-schema.org/) from default configuration

## Versions

- 0.2.2 fix equality
- 0.2.1 fix broken iterator
- 0.2 Config implements Mapping
- 0.1.1 handle NULL environment variables
- 0.1: basic proof of concept
