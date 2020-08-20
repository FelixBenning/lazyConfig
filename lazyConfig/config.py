#!/usr/bin/env python

from __future__ import annotations
from typing import Union
from collections.abc import Sequence, Mapping

from lazyConfig import LazyDict, LazyList


class Config:
    def __init__(self, default, config):
        self._default = default 
        self._config = config
    
    def __getattr__(self, name) -> Union[Config, ConfigList]:
        try:
            return self[name]
        except KeyError:
            raise AttributeError('no such configuration')

    def __getitem__(self, key):
        default = self._default[key]
        if isinstance(default, Mapping):
            config = self._config.get(key, default={})
            return Config(default, config) 
        elif isinstance(default, LazyList) or isinstance(default, list):
            if config := self._config.get(key):
                return ConfigList(config)
            else:
                return ConfigList(default)

        if config := self._config.get(key):
            return config
        
        return default
    
    def __dir__(self) -> list:
        return list(self._default.keys())
    
    def __repr__(self) -> str:
        return f"Config(default={repr(self._default)}, config={repr(self._config)})"
    
    def __str__(self) -> str:
        return f"configuration keys: {dir(self)}"

    @staticmethod
    def from_path(default_dir:str, config_dir:str) -> Config:
        return Config(LazyDict(default_dir), LazyDict(config_dir))
    
    # @classmethod
    # def from_environment()->Config:
    #     """ build from environment variables """
    #     pass
    
class ConfigList(Sequence):
    def __init__(self, raw_list:Union[list,LazyList]):
        self.list = raw_list
    
    def __getitem__(self, key):
        return Config(self.list[key], self.list[key])
    
    def __len__(self):
        return len(self.list)
    
    def __repr__(self):
        return f"ConfigList({repr(self.list)})"


    
if __name__ == "__main__":
    cfg = Config.from_path('test_config_default','test_config')
    l=cfg.list[0]
    l.zeroKey