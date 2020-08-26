import pytest

from lazyConfig import Config
import os

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


