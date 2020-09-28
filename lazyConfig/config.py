#!/usr/bin/env python

from __future__ import annotations
from typing import Union, List
from collections.abc import Sequence, Mapping
import os

from deprecation import deprecated

import lazyConfig
from .lazyData import LazyDict, LazyList

KEY_ERROR_NOTE = (
    'Note: you can only override existing keys. Document possible '
    'overrides in the default configuration with None values'
)

def override_mapping(target: Mapping, override: Mapping):
    """ override values for existing keys recursively leaving sister keys untouched

    Args:
        target (Mapping): mapping which's values are overriden (is modified!)
        override (Mapping): provides values for the override
    """
    for key in target:
        try:
            value = override[key]
        except KeyError:
            pass
        else:
            if isinstance(value, Mapping):
                override_mapping(target[key], value)
            elif isinstance(value, LazyList):
                target[key] = value.as_list()
            else:
                target[key] = value

def strip_none_from_mapping(mapping: Mapping):
    """ recursively strip None values from the (nested) Mapping """
    return {key: _recursive_strip(value) for key, value in mapping.items() if value is not None}

def _recursive_strip(possible_dict):
    if isinstance(possible_dict, Mapping):
        return strip_none_from_mapping(possible_dict)
    return possible_dict


def yield_values_for_key(list_of_dicts: List[Mapping], key):
    """ yield d[key] for every d in the list_of_dicts which do not throw a KeyError
    """
    for d in list_of_dicts:
        try:
            yield d[key]
        except KeyError:
            pass

class Config(Mapping):
    def __init__(self, config: Mapping, override: list):
        self._config = config
        self._override = override

    def __getattr__(self, name) -> Union[Config, ConfigList]:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f'no configuration called {name}.\n' + KEY_ERROR_NOTE
            ) from None

    def __getitem__(self, key):
        try:
            default = self._config[key]
        except KeyError:
            raise KeyError(
                f'the (default) configuration has no key {key}.\n'
                + KEY_ERROR_NOTE
            ) from None
        if isinstance(default, Mapping):
            config = [value for value in yield_values_for_key(self._override, key)]
            return Config(default, config)
        if isinstance(default, (LazyList, list)):
            for cfg in self._override[::-1]:
                try:
                    return ConfigList(cfg[key])
                except KeyError:
                    pass
            return ConfigList(default)

        for cfg in self._override[::-1]:
            try:
                return cfg[key]
            except KeyError:
                pass
        return default

    def as_primitive(self):
        """ alias for as_dict """
        return self.as_dict(strip_none=False)

    def as_dict(self, strip_none = True) -> dict:
        """return configuration as primitive dictionary, causes a force_load()
        to the underlying dictionary

        Args:
            strip_none (bool, optional): delete keys with value None. Defaults to True.

        Returns:
            dict: a dictionary composed from the default configuration and all overrides
        """        
        result = self._config # note that result and thus self._config is modified!
        if isinstance(result, LazyDict):
            result = result.as_dict()
        for cfg in self._override:
            if isinstance(cfg, LazyDict):
                cfg = cfg.as_dict()
            override_mapping(result, cfg)
        self._config = result
        self._override = []
        if strip_none:
            result = strip_none_from_mapping(result)
        return result

    def force_load(self):
        """ load all lazy Dictionaries and perform all overrides
        """        
        self.as_dict()

    def add_override(self, override:Mapping, none_can_override = False):
        """add another override to the list of overrides trumping all previous ones

        this can be used to override configuration with command line arguments

        Args:
            override (Mapping): the Mapping to append
            none_can_override (bool, optional): override every key even if the value
            in the override is None. Defaults to False to be naturally compatible with
            argparse.
        """
        if not none_can_override:
            override = {key:value for key, value in override.items() if value is not None}
        self._override.append(override)

    def __dir__(self) -> list:
        return list(self._config.keys())

    def __repr__(self) -> str:
        return f"Config(config={repr(self._config)}, override={repr(self._override)})"

    def __str__(self) -> str:
        return f"configuration keys: {dir(self)}"

    def __len__(self):
        return len(self._config)

    def __iter__(self):
        return iter(self._config)

    @staticmethod
    @deprecated(deprecated_in="0.3", removed_in="1.0", details="use lazyConfig.from_path() instead")
    def from_path(config: str, *override: str) -> Config:
        """build from path to configuration directories"""
        return lazyConfig.from_path(config, override)

    @staticmethod
    @deprecated(deprecated_in="0.3", removed_in="1.0", details="use lazyConfig.from_env() instead")
    def from_env(config: str, *override: str)->Config:
        """ build from environment variables """
        return lazyConfig.from_path(
            os.environ[config],
            [path for x in override if (path := os.environ.get(x))]
        )

class ConfigList(Sequence):
    def __init__(self, raw_list: Union[list, LazyList]):
        self.list = raw_list

    def __getitem__(self, key):
        res = self.list[key]
        if isinstance(res, Mapping):
            return Config(res, [])
        if isinstance(res, list):
            return ConfigList(res)
        return res

    def as_primitive(self):
        """ alias for as_list()"""
        return self.as_list()

    def as_list(self):
        """ returns a standard list, which can be serialized """
        if isinstance(self.list, list):
            return self.list
        return self.list.as_list()

    def __len__(self):
        return len(self.list)

    def __repr__(self):
        return f"ConfigList({repr(self.list)})"

    def __eq__(self, other):
        if (length:=len(self)) == len(other):
            for idx in range(length):
                if self[idx] != other[idx]:
                    return False
            return True
        return False
