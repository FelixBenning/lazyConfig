import os, yaml, json

from typing import Dict, Callable, Union
from _io import TextIOWrapper
from collections.abc import Sequence, Mapping

from .config import Config, ConfigList
from .lazyData import LazyList, LazyDict, DEFAULT_EXTENSION_MAP
from lazyConfig import LazyMode

def from_env(
    config:str, override:str = '', 
    laziness:LazyMode = LazyMode.CACHED,
    custom_extension_loader:Dict[str, Callable[[TextIOWrapper], Union[dict,list]]] = {}
) -> Config:
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
        laziness= laziness,
        custom_extension_loader=custom_extension_loader
    )

def from_path(
    config:str, override:list=[],
    laziness:LazyMode = LazyMode.CACHED,
    custom_extension_loader:Dict[str, Callable[[TextIOWrapper], Union[dict,list]]] = {}
) -> Config:
    """ build Config from path to configuration directories
    
    config: (required) path to (default) configuration directory as its
                contents
    override: list of paths to configuration directories overriding the
                `config` directory
    laziness: a mode from the enum LazyMode
    custom_extension_loader: a dictionary of file extensions and loader functions
                overriding the default loaders. E.g. {'yml': yaml.safe_load}    
    """
    ext_map = DEFAULT_EXTENSION_MAP.copy()
    ext_map.update(custom_extension_loader)
    extension_loader = {key:value for key,value in ext_map.items() if value}
    return(Config(
        config = LazyDict(config,laziness=laziness,extension_map=extension_loader),
        override = [LazyDict(x, laziness, extension_loader) for x in override]
    ))

def from_primitive(config, override:list = []) -> Config:
    """ build Config from primitive datatypes (dict/list)

    note: if config is a list, the last non-empty list in override is used an
    all other are ignored
    """
    if isinstance(config, Mapping):
        return Config(
            config,
            override
        )
    if isinstance(config, Sequence):
        for cfg_list in override[::-1]:
            if cfg_list:
                assert isinstance(cfg_list, Sequence), 'default is Sequence, override is not'
                return ConfigList(cfg_list)
        return ConfigList(config)
    raise ValueError("config is neither Mapping nor Sequence")