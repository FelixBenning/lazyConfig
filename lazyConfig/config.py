#!/usr/bin/env python

from __future__ import annotations
from typing import Union
from collections.abc import Sequence, Mapping, Iterator
import os

from lazyConfig import LazyDict, LazyList


class Config(Mapping):
    def __init__(self, config, *override):
        self._config = config 
        self._override = override
    
    def __getattr__(self, name) -> Union[Config, ConfigList]:
        try:
            return self[name]
        except KeyError:
            raise AttributeError('no such configuration')

    def __getitem__(self, key):
        default = self._config[key]
        if isinstance(default, Mapping):
            config = [value for x in self._override if (value:= x.get(key))]
            return Config(default, *config) 
        elif isinstance(default, LazyList) or isinstance(default, list):
            for cfg in self._override[::-1]:
                if config := cfg.get(key):
                    return ConfigList(config)
            return ConfigList(default)

        for cfg in self._override[::-1]:
            if config := cfg.get(key):
                return config
        return default 
    
    def __dir__(self) -> list:
        return list(self._config.keys())
    
    def __repr__(self) -> str:
        return f"Config(default={repr(self._config)}, config={repr(self._override)})"
    
    def __str__(self) -> str:
        return f"configuration keys: {dir(self)}"

    def __len__(self):
        return len(self._config)
    
    def __iter__(self):
        return ConfigIterator(self)

    @staticmethod
    def from_path(config:str, *override:str) -> Config:
        return Config(LazyDict(config), *[LazyDict(x) for x in override])
    
    @staticmethod
    def from_env(config:str, *override:str)->Config:
        """ build from environment variables """
        return Config.from_path(os.environ[config], *[env for x in override if (env:=os.environ.get(x))])
    
# TODO: possibly sufficient to return a LazyDictIterator of the _default dict
# as the iterator only needs to return the keys and the _default dict defines
# the keys available
class ConfigIterator(Iterator):
    def __init__(self, config:Config):
        self.defaultIter = iter(config._default)

    def __next__(self):
        return self.defaultIter.__next__()

class ConfigList(Sequence):
    def __init__(self, raw_list:Union[list,LazyList]):
        self.list = raw_list
    
    def __getitem__(self, key):
        res = self.list[key]
        if isinstance(res, Mapping):
            return Config(res)
        elif isinstance(res, list):
            return ConfigList(res)
        return res
    
    def __len__(self):
        return len(self.list)
    
    def __repr__(self):
        return f"ConfigList({repr(self.list)})"


    
if __name__ == "__main__":
    cfg = Config.from_path('test_config_default','test_config')
    l=cfg.list[0]
    l.zeroKey