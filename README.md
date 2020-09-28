# lazyConfig

[![PyPI version](https://badge.fury.io/py/lazyConfig.svg)](https://badge.fury.io/py/lazyConfig)
[![License: MPL
2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![codecov](https://codecov.io/gh/FelixBenning/lazyConfig/branch/master/graph/badge.svg)](https://codecov.io/gh/FelixBenning/lazyConfig)

> lazily loading and overriding configuration

lazyConfig is an opinionated configuration provider. It can load `.yml`, `.yaml`,
`.json` and `.toml` configuration files out of the box but can be extended with
custom loaders. Opinionated since it requires you to
structure your configuration in a certain way in order to work.

## Why lazyConfig?

see [Motivation](https://github.com/FelixBenning/lazyConfig/blob/master/Motivation.md)

## Usage

In order to load your configuration folder into a `dict` like structure, simply
point `lazyConfig` to the folder

```python
import lazyConfig

config = lazyConfig.from_path(
    config='/path/to/default/config',
    override=[
        '/path/to/override',
        '/path/to/another/override/',
        ...
    ]
)

# or with environment variables:

os.environ['CONFIG'] = '/path/to/default/config'
os.environ['CONFIG_OVERRIDE'] = f'/path/to/override/{os.pathsep}/path/to/another/override/'
config = lazyConfig.from_env()
```

You can change the envrionment variable names by passing their names, e.g.

```python
lazyConfig.from_env(config='DEFAULT_CONFIG', override='CONFIG')
```

Files are overriden left to right (i.e. the last argument has
priority)

> you could mix and match using `Config.from_path` and `os.environ['ENV_VAR']`

### Add override

If you are using an command line interface parser (e.g. argparse) to generate
a dictionary for overriding configuration, you might want to add an
additional override. You can use

```python
config.add_override(argparse_results)
```

where `argparse_results` is of type `Mapping`

> use `vars()` to obtain a `dict` from an `arparse.Namespace` which is the
return type of an arparse parser

arparse uses `None` to indicate missing configuration. So `add_override` ignores
`None` by default. If you provide the parameter `none_can_override=True`, you can
remove configuration with `None` values.

### Override Restrictions

You can only override keys which exist in the default configuration. This
requirement ensures that the default configuration documents all possible
configuration options. Use the value `None` in the default configuration for
settings you do not want to select a default for. You can obtain a dict without
these entries with

```python
config.as_dict(strip_none=True)
```

> `strip_none=True` is the default, set it to false if you want a dict
including all `None` values

### Assumptions about the file structure

Filenames are used as keys in the `config` dict, so without any caveats
you would be forced to have a minimum depth of `1` for any configuration.

This might not make sense for some high level, flat configuration. For this
reason there is a special filename `__config__` (`.yml`,`.yaml`, `.json`,...),
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

### Attribute access

You could then access `index1` with:

```python
config.database.configuration.indices.index1
```

Python does not allow attributes to start with a number. So

```python
config.1attribute2breakthings
```

will not work. In these cases you will have to use

```python
config['1attribute2breakthings']
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
Pass a `custom_extension_loader` to the factory method:

```python
lazyConfig.from_path('path/to/config', custom_extension_loader={
    '.yml': yaml.safe_load,
    '.yaml': yaml.safe_load
})
```

This overrides the yaml loader while leaving the other loaders in place. To remove
a default loader, override the extension with a Falsy value (e.g. `None`)

## Future Features

things which I might get around to do some time:

- Configuration Validation
- Horizontal override (Templates, e.g. for indices)
- Configuration Setter
    > Since it is not obvious where to set directory/file boundaries inside the
    dictionary, this is not as trivial as it might seem at first. It might be
    necessary to provide the grouping level as an argument.
- generate [JSON Schema](https://json-schema.org/) from default configuration

## Versions

- 0.5 proper none handling
- 0.4 add_overwrite
- 0.3 as_primitive, as_dict, as_list, laziness modes and custom loader, TOML support
- 0.2.2 fix equality
- 0.2.1 fix broken iterator
- 0.2 Config implements Mapping
- 0.1.1 handle NULL environment variables
- 0.1: basic proof of concept
