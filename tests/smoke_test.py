import pytest

import lazyConfig
from lazyConfig import Config, ConfigList, LazyMode
import os, yaml, json, toml

def test_createConfig():
    cfg = Config.from_path('tests/config_default')

    assert isinstance(cfg, Config), "could not create config"
    assert cfg.list[1].oneKey == 'oneValue'
    assert cfg.version == -1.0
    assert cfg.database.connection.hosts[0].host == "localhost" 

    os.environ['TEST'] = 'tests/config'
    config = Config.from_env('TEST')
    repr(config)
    print(config)
    dir(config)

    # second and later variables may be unset/empty
    os.environ['Empty'] = ''
    lazyConfig.from_env('TEST', 'Empty')
    del os.environ['Empty']
    config = lazyConfig.from_env('TEST', 'Empty')

    # is Mapping
    config.items()
    iter(config)

def test_override():
    print('test_override')
    cfg = lazyConfig.from_path('tests/config_default', ['tests/config'])

    # list overridden 
    assert cfg.list[0] == 'haha'
    with pytest.raises(IndexError):
        print(cfg.list[1])
    
    assert cfg.app.primary_color == 'pink'
    assert cfg.version == 42
    assert cfg.database.configuration.indices.index1 == 'overridden index'
    assert cfg.database.connection.hosts[0].host == "myElasticsearchServer" 
    
    #not overridden
    assert cfg.author == 'ME!'
    assert cfg.database.configuration.indices.index2 == 'stayIndex'

    cfg.add_override({'author': 'not ME!', 'version': None})
    
    assert cfg.author == 'not ME!'
    assert cfg.version == 42


def test_equality():
    l_std = [1,2,3,'test', False]
    l_cfg = lazyConfig.from_primitive(l_std)

    assert l_std == l_cfg, "list == ConfigList(list) equality is broken"
    assert l_cfg == l_std, "ConfigList(list) == list equality is broken"

    assert lazyConfig.from_primitive([]) == [], 'empty list equality is broken'

    with open("tests/config/database/__config__.yml", 'r') as f:
        std_dict_connection = yaml.unsafe_load(f)['connection']
    
    config_connection = lazyConfig.from_path('tests/config').database.connection

    assert std_dict_connection == config_connection, 'Config equality is broken'

    config_override = lazyConfig.from_path('tests/config_default', ['tests/config'])
    assert config_override.database.connection == config_connection, 'Override is broken'

    d = config_override.as_dict()
    assert d == config_override, 'as_dict is broken'
    
    json.dumps(d)

def test_properties():
    config = lazyConfig.from_path('tests/config_default', ['tests/config'])
    count = 0
    for _ in config:
        count += 1
    
    assert count == len(config), "length is broken"

    config_override_lazy = lazyConfig.from_path('tests/config_default', ['tests/config'], laziness=LazyMode.LAZY)
    lazy_dict = config_override_lazy.as_dict()
    assert config == lazy_dict, 'laziness breaks'

def test_lists():
    config = lazyConfig.from_path('tests/config_default')
    assert config.list[-1] == config.list[len(config.list)-1], 'negative indices broken'
    assert config.list[1:5] == config.list[1:2], 'oversized ranges broken'
    assert config.list[0,1] == config.list, 'tuples broken'

    prim_list = config.list.as_list()
    assert config.as_primitive()['list'] == prim_list

def test_toml():
    config = lazyConfig.from_path('tests/config_toml')
    with open('tests/config_toml/__config__.toml', 'r') as f:
        assert config == toml.loads(f.read())