from advanced_alchemy.extensions.fastapi import AdvancedAlchemy

from todo_api.core.database.base import sqlalchemy_async_config, sqlalchemy_sync_config

alchemy_async = AdvancedAlchemy(config=sqlalchemy_async_config, app=None)
alchemy_sync = AdvancedAlchemy(config=sqlalchemy_sync_config, app=None)
