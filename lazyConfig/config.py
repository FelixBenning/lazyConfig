#!/usr/bin/env python

from __future__ import annotations
from typing import Union
from collections.abc import Sequence, Mapping, Iterator
import os, yaml, json
from deprecation import deprecated

from lazyConfig import LazyDict, LazyList, LazyMode

DEFAULT_EXTENSION_MAP = {
    'yml': yaml.unsafe_load,
    'yaml': yaml.unsafe_load,
    'json': json.load
}

class Config(Mapping):
    def __init__(
        self, config:Mapping, override:list, extension_loader:dict, laziness:LazyMode
    ):
        self._config = config
        self._override = override
        self.laziness = laziness
        self._extension_loader = extension_loader

    def __getattr__(self, name) -> Union[Config, ConfigList]:
        try:
            return self[name]
        except KeyError as err:
            raise AttributeError('no such configuration') from err

    def __getitem__(self, key):
        default = self._config[key]
        if isinstance(default, Mapping):
            config = [value for x in self._override if (value:= x.get(key))]
            return Config(default, config, self._extension_loader, self.laziness)
        if isinstance(default, (LazyList, list)):
            for cfg in self._override[::-1]:
                if cfg_lst := cfg.get(key):
                    return ConfigList(cfg_lst, self._extension_loader, self.laziness)
            return ConfigList(default, self._extension_loader, self.laziness)

        for cfg in self._override[::-1]:
            if config := cfg.get(key):
                return config
        return default

    def __dir__(self) -> list:
        return list(self._config.keys())

    def __repr__(self) -> str:
        return (f"Config(config={repr(self._config)}, override={repr(self._override)},"
            f"laziness={self.laziness}, extension_loader={self._extension_loader})")

    def __str__(self) -> str:
        return f"configuration keys: {dir(self)}"

    def __len__(self):
        return len(self._config)

    def __iter__(self):
        return ConfigIterator(self)

    @staticmethod
    @deprecated(deprecated_in="0.3", removed_in="1.0", details="use lazyConfig.from_path() instead")
    def from_path(config:str, *override:str) -> Config:
        """build from path to configuration directories"""
        return from_path(config, override)

    @staticmethod
    @deprecated(deprecated_in="0.3", removed_in="1.0", details="use lazyConfig.from_env() instead")
    def from_env(config:str, *override:str)->Config:
        """ build from environment variables """
        return from_path(
            os.environ[config],
            [path for x in override if (path:=os.environ.get(x))]
        )


def from_env(
    config:str, override:str = '', 
    laziness:LazyMode = LazyMode.cached,
    custom_extension_loader:dict = {}
):
    """ build Config from environment variables 
    
    config: (required) environment variable with path to (default) configuration
                directory as its contents
    override: env var pointing to os.pathsep (':' linux, ';' win) separated paths
                configuration directories overriding the `config` directory
    laziness: a mode from the enum LazyMode
    custom_extension_loader: a dictionary of file extensions and loader functions
                overriding the default loaders. E.g. {'yml': yaml.safe_load}    
    """
    override_list = []
    
    if path_list:=os.environ.get(override):
        override_list = path_list.split(sep=os.pathsep)

    return from_path(
        config = os.environ[config],
        override = override_list,
        laziness = laziness,
        custom_extension_loader = custom_extension_loader
    )

def from_path(
    config:str, override:list=[],
    laziness:LazyMode = LazyMode.cached,
    custom_extension_loader:dict = {}
):
    """ build Config from path to configuration directories
    
    config: (required) path to (default) configuration directory as its
                contents
    override: list of paths to configuration directories overriding the
                `config` directory
    laziness: a mode from the enum LazyMode
    custom_extension_loader: a dictionary of file extensions and loader functions
                overriding the default loaders. E.g. {'yml': yaml.safe_load}    
    """
    (extension_loader := DEFAULT_EXTENSION_MAP.copy()).update(custom_extension_loader)
    return(Config(
        config = LazyDict(config),
        override = [LazyDict(x) for x in override],
        laziness = laziness,
        extension_loader = extension_loader
    ))

def from_primitive(config, override:list = []):
    if isinstance(config, Mapping):
        return Config(config, override, DEFAULT_EXTENSION_MAP.copy(), LazyMode.eager)
    if isinstance(config, Sequence):
        for cfg_list in override[::-1]:
            if cfg_list:
                assert isinstance(cfg_list, Sequence), 'default is Sequence, override is not'
                return ConfigList(cfg_list, DEFAULT_EXTENSION_MAP.copy(), LazyMode.eager)
        return ConfigList(config, DEFAULT_EXTENSION_MAP.copy(), LazyMode.eager)
    raise ValueError("config is neither Mapping nor Sequence")
        


# TODO: possibly sufficient to return a LazyDictIterator of the _config dict
# as the iterator only needs to return the keys and the _config dict defines
# the keys available
class ConfigIterator(Iterator):
    def __init__(self, config:Config):
        self.default_iter = iter(config._config)

    def __next__(self):
        return self.default_iter.__next__()

class ConfigList(Sequence):
    def __init__(
        self, raw_list:Union[list,LazyList], extension_loader:dict, laziness:LazyMode
    ):
        self.list = raw_list
        self.laziness = laziness
        self._extension_loader = extension_loader

    def __getitem__(self, key):
        res = self.list[key]
        if isinstance(res, Mapping):
            return Config(res, [], self._extension_loader, self.laziness)
        if isinstance(res, list):
            return ConfigList(res, self._extension_loader, self.laziness)
        return res

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
