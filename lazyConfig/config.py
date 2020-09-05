#!/usr/bin/env python

from __future__ import annotations
from typing import Union
from collections.abc import Sequence, Mapping, Iterator
import os, yaml, json

from deprecation import deprecated

from .lazyData import LazyDict, LazyList, LazyMode
import lazyConfig


def override(old:Mapping, new:Mapping):
    """ override values recursively leaving sister keys untouched """
    for key, value in new.items():
        if isinstance(value, Mapping):
            override(old[key], value)
        elif isinstance(value, LazyList):
            old[key] = value.as_list()
        else:
            old[key] = value

class Config(Mapping):
    def __init__(
        self, config:Mapping, override:list
    ):
        self._config = config
        self._override = override

    def __getattr__(self, name) -> Union[Config, ConfigList]:
        try:
            return self[name]
        except KeyError as err:
            raise AttributeError('no such configuration') from err

    def __getitem__(self, key):
        default = self._config[key]
        if isinstance(default, Mapping):
            config = [value for x in self._override if (value:= x.get(key))]
            return Config(default, config)
        if isinstance(default, (LazyList, list)):
            for cfg in self._override[::-1]:
                if cfg_lst := cfg.get(key):
                    return ConfigList(cfg_lst)
            return ConfigList(default)

        for cfg in self._override[::-1]:
            if config := cfg.get(key):
                return config
        return default

    def as_primitive(self):
        """ alias for as_dict """
        return self.as_dict()
    
    def as_dict(self):
        result = self._config
        if isinstance(result, LazyDict):
            result = result.as_dict()
        for cfg in self._override:
            if isinstance(cfg, LazyDict):
                cfg = cfg.as_dict()
            override(result, cfg)
        return result
    
    def force_load(self):
        self._config = self.as_dict()
        self._override = []

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
    def from_path(config:str, *override:str) -> Config:
        """build from path to configuration directories"""
        return lazyConfig.from_path(config, override)

    @staticmethod
    @deprecated(deprecated_in="0.3", removed_in="1.0", details="use lazyConfig.from_env() instead")
    def from_env(config:str, *override:str)->Config:
        """ build from environment variables """
        return lazyConfig.from_path(
            os.environ[config],
            [path for x in override if (path:=os.environ.get(x))]
        )

class ConfigList(Sequence):
    def __init__(
        self, raw_list:Union[list,LazyList] 
    ):
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
        else:
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

