import datetime
from operator import attrgetter

import psycopg2
import psycopg2.extras

from file_manager.config import settings, VERSION, LOG
from file_manager.data.base_engine import BaseEngine
from file_manager.data.field import Field
from file_manager.data.models import find_model
from file_manager.data.query import Query


class PsycoPGEngine(BaseEngine):
    @classmethod
    def setup_model(cls, model_class):
        """
        :type model_class: Type[BaseModel]
        """
        assert model_class.NAME is not None, 'Model %s does not have a NAME.' % model_class

        conn = PsycoPGEngine._connect()
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE TABLE "%s" (id SERIAL PRIMARY KEY NOT NULL);' % model_class.NAME)
        except psycopg2.ProgrammingError as e:
            if 'already exists' in str(e):
                LOG.debug('Table %s already exists.' % model_class.NAME)
            else:
                raise

        for field in model_class.fields():
            if not isinstance(field, Field) or field.name == 'id':
                continue
            try:
                cursor.execute('ALTER TABLE "%s" ADD COLUMN "%s" %s;' % (model_class.NAME, field.name,
                                                                         PsycoPGEngine._map_type(field.type)))
            except psycopg2.ProgrammingError as e:
                if 'already exists' in str(e):
                    LOG.debug('Column %s.%s already exists.' % (model_class.NAME, field.name))
                else:
                    raise

    @classmethod
    def create(cls, model):
        """
        :type model: BaseModel
        :param model: Populated model to make an entry for
        """
        assert model.id is None, 'Record [%s] already created.' % model.id

        fields = model.fields()
        columns = [field.name for field in fields if field.name != 'id']

        data = model.data()
        data['timestamp'] = datetime.datetime.now()
        data.pop('id', None)
        for k, v in data.items():
            data[k] = str(v) if v not in (0, None, '') else None

        model_values = [data[k] for k in columns]

        values = ('%s,' * len(columns)).rstrip(',')
        statement = "INSERT INTO %s(%s) VALUES (%s) RETURNING *" % (model.NAME, ', '.join(columns), values)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, model_values))
            cursor.execute(statement, model_values)
            new_data = cursor.fetchall()[0]
            # Apply new data
            for k, v in new_data.items():
                setattr(model, k, v)
            model.clear_changes()
        finally:
            conn.close()

    @classmethod
    def create_many(cls, models):
        assert all(x.id is None for x in models), 'Some models already exist.'

        model_name = models[0].NAME
        columns = [field.name for field in models[0].fields() if field.name != 'id']

        all_values = list()
        for model in models:
            _data = model.data()
            _data['timestamp'] = datetime.datetime.now()
            _data.pop('id', None)
            for k, v in _data.items():
                _data[k] = str(v) if v not in (0, None, '') else None
            model_values = [_data[k] for k in columns]
            all_values.extend(model_values)

        _arg_string = ('%s,' * len(columns)).rstrip(',')
        values = ['(%s)' % _arg_string] * len(models)
        statement = "INSERT INTO %s(%s) VALUES %s RETURNING *" % (model_name, ', '.join(columns), ','.join(values))
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, all_values))
            cursor.execute(statement, all_values)
            new_records = cursor.fetchall()

            # Apply new data
            for model, data in zip(models, new_records):
                for k, v in data.items():
                    setattr(model, k, v)
                model.clear_changes()
        finally:
            conn.close()

    @classmethod
    def select(cls, query):
        """
        :type query: file_manager.data.query.Query
        :rtype: list[file_manager.data.base_model.BaseModel]
        """
        statement = query.build_query(query.DBLANG.POSTGRES)
        model = find_model(query.table())

        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(statement)
            result = cursor.fetchall()
            LOG.debug('%s - Found %d records.' % (cursor.mogrify(statement), len(result)))
            return [model(**r) for r in result]
        finally:
            conn.close()

    @classmethod
    def update(cls, model):
        """
        :type model: BaseModel
        :rtype: list[dict[str,variant]]
        """
        assert model.id is not None, 'Record has not been created.'

        changes = model.changes()
        columns = changes.keys()
        values = changes.values()
        values = [str(v) if v not in (0, None, '') else None for v in values]

        set_data = ['"%s"=%%s' % column for column in columns]

        statement = "UPDATE %s SET %s WHERE id=%s RETURNING *" % (model.NAME, ', '.join(set_data), model.id)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement, values))
            cursor.execute(statement, values)
            new_data = cursor.fetchall()[0]
            # Apply new data
            for k, v in new_data.items():
                setattr(model, k, v)
            model.clear_changes()
        finally:
            conn.close()

    @classmethod
    def update_many(cls, models):
        """
        :type model: list[BaseModel]
        :rtype: list[dict[str,variant]]
        """
        assert all(x.id is not None for x in models), 'Some models have not been created.'

        models = models[:]
        models.sort(key=attrgetter('id'))
        model_name = models[0].NAME

        cmd_value_pairs = list()
        for model in models:
            changes = model.changes()
            columns = changes.keys()
            values = changes.values()
            values = [str(v) if v not in (0, None, '') else None for v in values]

            set_data = ['"%s"=%%s' % column for column in columns]

            columns = [field.name for field in models[0].fields() if field.name != 'id']

            all_values = list()
            for model in models:
                _data = model.data()
                _data['timestamp'] = datetime.datetime.now()
                _data.pop('id', None)
                for k, v in _data.items():
                    _data[k] = str(v) if v not in (0, None, '') else None
                model_values = [_data[k] for k in columns]
                all_values.extend(model_values)

            statement = "UPDATE %s SET %s WHERE id=%s;" % (model_name, ', '.join(set_data), model.id)
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

            refresh_records = PsycoPGEngine.select(Query(model_name, id=[_.id for _ in models]))
            refresh_records.sort(key=attrgetter('id'))

            assert len(models) == len(refresh_records), 'Updated model count does not match refresh count.'

            # Apply new data
            for model, new_model in zip(models, refresh_records):
                for k, v in new_model.data():
                    setattr(model, k, v)
                model.clear_changes()
        finally:
            conn.close()

        # statement = "UPDATE %s SET %s WHERE id=%s RETURNING *" % (model.NAME, ', '.join(set_data), model.id)
        # conn = PsycoPGEngine._connect()
        # try:
        #     cursor = conn.cursor()
        #     LOG.debug(cursor.mogrify(statement, values))
        #     cursor.execute(statement, values)
        #     new_data = cursor.fetchall()[0]
        #     # Apply new data
        #     for k, v in new_data.items():
        #         setattr(model, k, v)
        #     model.clear_changes()
        # finally:
        #     conn.close()

    @classmethod
    def delete(cls, model):
        """
        :type model: BaseModel
        """
        assert model.id is not None, 'Record has not been created.'

        statement = "DELETE FROM %s WHERE id=%s" % (model.NAME, model.id)
        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement))
            cursor.execute(statement)
            model.id = None
            model.clear_changes()
        finally:
            conn.close()

    @classmethod
    def delete_many(cls, models):
        """
        :type models: list[BaseModel]
        """
        if not models:
            return

        assert all(x.id is not None for x in models), 'Some models have not been created.'

        if len(models) > 1:
            ids = tuple([_.id for _ in models])
            statement = "DELETE FROM %s WHERE id in %s" % (models[0].NAME, str(ids))
        else:
            statement = "DELETE FROM %s WHERE id = %s" % (models[0].NAME, models[0].id)

        conn = PsycoPGEngine._connect()
        try:
            cursor = conn.cursor()
            LOG.debug(cursor.mogrify(statement))
            cursor.execute(statement)
            for model in models:
                model.id = None
                model.clear_changes()
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
