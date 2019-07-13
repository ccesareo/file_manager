import datetime
import os
import re
import sqlite3
from operator import attrgetter

from .base_engine import BaseEngine
from ..entities import find_entity
from ..field import Field
from ..query import Query
from ...config import settings, LOG


class SqliteEngine(BaseEngine):
    @classmethod
    def setup_entity(cls, entity_class):
        """
        :type entity_class: Type[BaseEntity]
        """
        assert entity_class.NAME is not None, 'Entity %s does not have a NAME.' % entity_class

        conn = SqliteEngine._connect()
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE "%s" (id INTEGER PRIMARY KEY NOT NULL);' % entity_class.NAME)
        except sqlite3.Error as e:
            if 'already exists' in str(e) or 'duplicate column name' in str(e):
                LOG.debug('Table %s already exists.' % entity_class.NAME)
            else:
                raise

        for field in entity_class.fields():
            if not isinstance(field, Field) or field.name == 'id':
                continue
            try:
                cursor.execute('ALTER TABLE "%s" ADD COLUMN "%s" %s;' % (entity_class.NAME, field.name,
                                                                         SqliteEngine._map_type(field.type)))
            except sqlite3.Error as e:
                if 'already exists' in str(e) or 'duplicate column name' in str(e):
                    LOG.debug('Column %s.%s already exists.' % (entity_class.NAME, field.name))
                else:
                    raise

    @classmethod
    def create(cls, entity):
        """
        :type entity: file_manager.data.base_entity.BaseEntity
        :param entity: Populated entity to make an entry for
        """
        assert entity.id is None, 'Record [%s] already created.' % entity.id

        fields = entity.fields()
        columns = [field.name for field in fields if field.name != 'id']

        data = entity.data()
        data['timestamp'] = datetime.datetime.now()
        data.pop('id', None)
        for k, v in data.items():
            data[k] = str(v) if v not in (0, None, '') else None

        entity_values = [data[k] for k in columns]

        values = ('?,' * len(columns)).rstrip(',')
        statement = "INSERT INTO %s(%s) VALUES (%s)" % (entity.NAME, ', '.join(columns), values)
        conn = SqliteEngine._connect()
        try:
            cursor = conn.cursor()
            # LOG.debug(statement % tuple(entity_values))
            cursor.execute(statement, entity_values)
            last_id = cursor.lastrowid
        finally:
            conn.commit()
            conn.close()

        new_entity = cls.select(Query(entity.NAME, id=int(last_id)))[0]
        # Apply new data
        for k, v in new_entity.data().items():
            setattr(entity, k, v)
        entity.clear_changes()

    @classmethod
    def create_many(cls, entities):
        assert all(x.id is None for x in entities), 'Some entities already exist.'

        # SQLite cannot return multiple results back from an INSERT many statement
        for entity in entities:
            cls.create(entity)

    @classmethod
    def select(cls, query):
        """
        :type query: file_manager.data.query.Query
        :rtype: list[file_manager.data.base_entity.BaseEntity]
        """
        statement = query.build_query(query.DBLANG.SQLITE)
        entity = find_entity(query.table())

        conn = SqliteEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(statement)
            cursor.execute(statement)
            result = cursor.fetchall()
            LOG.debug('%s - Found %d records.' % (statement, len(result)))
            return [entity(**r) for r in result]
        finally:
            conn.commit()
            conn.close()

    @classmethod
    def update(cls, entity):
        """
        :type entity: BaseEntity
        :rtype: list[dict[str,variant]]
        """
        assert entity.id is not None, 'Record has not been created.'

        cls.update_many([entity])

    @classmethod
    def update_many(cls, entities):
        """
        :type entities: list[BaseEntity]
        :rtype: list[dict[str,variant]]
        """
        assert all(x.id is not None for x in entities), 'Some entities have not been created.'

        entities = entities[:]
        entities.sort(key=attrgetter('id'))
        entity_name = entities[0].NAME

        cmd_value_pairs = list()
        for entity in entities:
            changes = entity.changes()
            columns = changes.keys()
            values = changes.values()
            values = [str(v) if v not in (0, None, '') else None for v in values]

            set_data = ['"%s"=?' % column for column in columns]

            columns = [field.name for field in entities[0].fields() if field.name != 'id']

            all_values = list()
            for _entity in entities:
                _data = _entity.data()
                _data['timestamp'] = datetime.datetime.now()
                _data.pop('id', None)
                for k, v in _data.items():
                    _data[k] = str(v) if v not in (0, None, '') else None
                entity_values = [_data[k] for k in columns]
                all_values.extend(entity_values)

            statement = "UPDATE %s SET %s WHERE id=%s;" % (entity_name, ', '.join(set_data), entity.id)
            cmd_value_pairs.append((statement, values))

        conn = SqliteEngine._connect()
        try:
            cursor = conn.cursor()
            statements = list()
            all_values = list()
            for cmd, values in cmd_value_pairs:
                LOG.debug(cmd)
                statements.append(cmd)
                all_values.extend(values)
            cursor.execute('\n'.join(statements), all_values)

            refresh_records = SqliteEngine.select(Query(entity_name, id=[_.id for _ in entities]))
            refresh_records.sort(key=attrgetter('id'))

            assert len(entities) == len(refresh_records), 'Updated entity count does not match refresh count.'

            # Apply new data
            for entity, new_entity in zip(entities, refresh_records):
                for k, v in new_entity.data().items():
                    setattr(entity, k, v)
                entity.clear_changes()
        finally:
            conn.commit()
            conn.close()

        # statement = "UPDATE %s SET %s WHERE id=%s RETURNING *" % (entity.NAME, ', '.join(set_data), entity.id)
        # conn = SqliteEngine._connect()
        # try:
        #     cursor = conn.cursor()
        #     LOG.debug(cursor.mogrify(statement, values))
        #     cursor.execute(statement, values)
        #     new_data = cursor.fetchall()[0]
        #     # Apply new data
        #     for k, v in new_data.items():
        #         setattr(entity, k, v)
        #     entity.clear_changes()
        # finally:
        #     conn.commit()
        #     conn.close()

    @classmethod
    def delete(cls, entity):
        """
        :type entity: BaseEntity
        """
        assert entity.id is not None, 'Record has not been created.'

        statement = "DELETE FROM %s WHERE id=%s" % (entity.NAME, entity.id)
        conn = SqliteEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(statement)
            cursor.execute(statement)
            entity.id = None
            entity.clear_changes()
        finally:
            conn.commit()
            conn.close()

    @classmethod
    def delete_many(cls, entities):
        """
        :type entities: list[BaseEntity]
        """
        if not entities:
            return

        assert all(x.id is not None for x in entities), 'Some entities have not been created.'

        if len(entities) > 1:
            ids = tuple([_.id for _ in entities])
            statement = "DELETE FROM %s WHERE id in %s" % (entities[0].NAME, str(ids))
        else:
            statement = "DELETE FROM %s WHERE id = %s" % (entities[0].NAME, entities[0].id)

        conn = SqliteEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(statement)
            cursor.execute(statement)
            for entity in entities:
                entity.id = None
                entity.clear_changes()
        finally:
            conn.commit()
            conn.close()

    @staticmethod
    def _connect():
        """
        :rtype: psycopg2.psycopg1.cursor
        """
        assert os.path.isfile(settings.db_host), 'Please set the database file path to "host" in settings.ini.'
        conn = sqlite3.connect(settings.db_host)
        conn.row_factory = sqlite3.Row
        conn.create_function("REGEXP", 2, _regexp)
        return conn

    @staticmethod
    def _map_type(typ):
        if typ in (str,):
            return 'TEXT'
        elif typ in (int,):
            return 'INTEGER'
        elif typ in (float,):
            return 'DOUBLE PRECISION'
        elif typ in (datetime.date,):
            return 'DATE'
        elif typ in (datetime.datetime,):
            return 'TIMESTAMP WITH TIME ZONE'
        else:
            raise Exception('Invalid type %s, could not map to engine.' % typ)


def _regexp(expr, item):
    return re.compile(expr).search(item) is not None
