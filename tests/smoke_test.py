import pytest

from lazyConfig import Config, ConfigList
import os, yaml

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
    Config.from_env('TEST', 'Empty')
    del os.environ['Empty']
    config = Config.from_env('TEST', 'Empty')

    # is Mapping
    config.items()
    iter(config)

def test_override():
    cfg = Config.from_path('tests/config_default', 'tests/config')

    # list overriden 
    assert cfg.list[0] == 'haha'
    with pytest.raises(IndexError):
        print(cfg.list[1])
    
    assert cfg.app.primary_color == 'pink'
    assert cfg.version == 42
    assert cfg.database.configuration.indices.index1 == 'overridden index'
    assert cfg.database.connection.hosts[0].host == "myElasticsearchServer" 
    
    #not overriden
    assert cfg.author == 'ME!'
    assert cfg.database.configuration.indices.index2 == 'stayIndex'


def test_equality():
    l_std = [1,2,3,'test', False]
    l_cfg = ConfigList(l_std)

    assert l_std == l_cfg, "list == ConfigList(list) equality is broken"
    assert l_cfg == l_std, "ConfigList(list) == list equality is broken"

    assert ConfigList([]) == [], 'empty list equality is broken'

    with open("tests/config/database/__config__.yml", 'r') as f:
        std_dict_connection = yaml.load(f)['connection']
    
    config_connection = Config.from_path('tests/config').database.connection

    assert std_dict_connection == config_connection, 'Config equality is broken'
