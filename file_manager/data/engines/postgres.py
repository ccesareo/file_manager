import datetime
from operator import attrgetter

import psycopg2
import psycopg2.extras

from .base_engine import BaseEngine
from ...config import settings, VERSION, LOG
from ...data.entities import find_entity
from ...data.field import Field
from ...data.query import Query


class PsycoPGEngine(BaseEngine):
    @classmethod
    def setup_entity(cls, entity_class):
        """
        :type entity_class: Type[BaseEntity]
        """
        assert entity_class.NAME is not None, 'Entity %s does not have a NAME.' % entity_class

        conn = PsycoPGEngine._connect()
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE "%s" (id SERIAL PRIMARY KEY NOT NULL);' % entity_class.NAME)
        except psycopg2.ProgrammingError as e:
            if 'already exists' in str(e):
                LOG.debug('Table %s already exists.' % entity_class.NAME)
            else:
                raise

        for field in entity_class.fields():
            if not isinstance(field, Field) or field.name == 'id':
                continue
            try:
                cursor.execute('ALTER TABLE "%s" ADD COLUMN "%s" %s;' % (entity_class.NAME, field.name,
                                                                         PsycoPGEngine._map_type(field.type)))
            except psycopg2.ProgrammingError as e:
                if 'already exists' in str(e):
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

        values = ('%s,' * len(columns)).rstrip(',')
        statement = "INSERT INTO %s(%s) VALUES (%s) RETURNING *" % (entity.NAME, ', '.join(columns), values)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, entity_values))
            cursor.execute(statement, entity_values)
            new_data = cursor.fetchall()[0]
            # Apply new data
            for k, v in new_data.items():
                setattr(entity, k, v)
            entity.clear_changes()
        finally:
            conn.close()

    @classmethod
    def create_many(cls, entities):
        assert all(x.id is None for x in entities), 'Some entities already exist.'

        entity_name = entities[0].NAME
        columns = [field.name for field in entities[0].fields() if field.name != 'id']

        all_values = list()
        for entity in entities:
            _data = entity.data()
            _data['timestamp'] = datetime.datetime.now()
            _data.pop('id', None)
            for k, v in _data.items():
                _data[k] = str(v) if v not in (0, None, '') else None
            entity_values = [_data[k] for k in columns]
            all_values.extend(entity_values)

        _arg_string = ('%s,' * len(columns)).rstrip(',')
        values = ['(%s)' % _arg_string] * len(entities)
        statement = "INSERT INTO %s(%s) VALUES %s RETURNING *" % (entity_name, ', '.join(columns), ','.join(values))
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, all_values))
            cursor.execute(statement, all_values)
            new_records = cursor.fetchall()

            # Apply new data
            for entity, data in zip(entities, new_records):
                for k, v in data.items():
                    setattr(entity, k, v)
                entity.clear_changes()
        finally:
            conn.close()

    @classmethod
    def select(cls, query):
        """
        :type query: file_manager.data.query.Query
        :rtype: list[file_manager.data.base_entity.BaseEntity]
        """
        statement = query.build_query(query.DBLANG.POSTGRES)
        entity = find_entity(query.table())

        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(statement)
            cursor.execute(statement)
            result = cursor.fetchall()
            LOG.debug('%s - Found %d records.' % (cursor.mogrify(statement), len(result)))
            return [entity(**r) for r in result]
        finally:
            conn.close()

    @classmethod
    def update(cls, entity):
        """
        :type entity: BaseEntity
        :rtype: list[dict[str,variant]]
        """
        assert entity.id is not None, 'Record has not been created.'

        changes = entity.changes()
        columns = changes.keys()
        values = changes.values()
        values = [str(v) if v not in (0, None, '') else None for v in values]

        set_data = ['"%s"=%%s' % column for column in columns]

        statement = "UPDATE %s SET %s WHERE id=%s RETURNING *" % (entity.NAME, ', '.join(set_data), entity.id)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, values))
            cursor.execute(statement, values)
            new_data = cursor.fetchall()[0]
            # Apply new data
            for k, v in new_data.items():
                setattr(entity, k, v)
            entity.clear_changes()
        finally:
            conn.close()

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

            set_data = ['"%s"=%%s' % column for column in columns]

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

        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            statements = list()
            for cmd, values in cmd_value_pairs:
                statement = cursor.mogrify(cmd, values)
                statements.append(statement)
                LOG.debug(statement)
            cursor.execute('\n'.join(statements))

            refresh_records = PsycoPGEngine.select(Query(entity_name, id=[_.id for _ in entities]))
            refresh_records.sort(key=attrgetter('id'))

            assert len(entities) == len(refresh_records), 'Updated entity count does not match refresh count.'

            # Apply new data
            for entity, new_entity in zip(entities, refresh_records):
                for k, v in new_entity.data():
                    setattr(entity, k, v)
                entity.clear_changes()
        finally:
            conn.close()

        # statement = "UPDATE %s SET %s WHERE id=%s RETURNING *" % (entity.NAME, ', '.join(set_data), entity.id)
        # conn = PsycoPGEngine._connect()
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
        #     conn.close()

    @classmethod
    def delete(cls, entity):
        """
        :type entity: BaseEntity
        """
        assert entity.id is not None, 'Record has not been created.'

        statement = "DELETE FROM %s WHERE id=%s" % (entity.NAME, entity.id)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement))
            cursor.execute(statement)
            entity.id = None
            entity.clear_changes()
        finally:
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

        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement))
            cursor.execute(statement)
            for entity in entities:
                entity.id = None
                entity.clear_changes()
        finally:
            conn.close()

    @staticmethod
    def _connect():
        """
        :rtype: psycopg2.psycopg1.cursor
        """
        conn = psycopg2.connect(
            host=settings.db_host,
            user=settings.db_user,
            password=settings.db_pass,
            database=settings.db_name,
            port=settings.db_port,
            cursor_factory=psycopg2.extras.RealDictCursor,
            application_name='File Manager %s' % VERSION,
            connect_timeout=5
        )
        conn.autocommit = True
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
