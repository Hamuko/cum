from abc import ABCMeta, abstractmethod
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql import sqltypes


class DatabaseSanity(object):
    """Class designed for database validation and repair."""

    def __init__(self, base, engine):
        self.base = base
        self.engine = engine
        self.errors = []
        self.inspection_engine = inspect(self.engine)

    @property
    def database_tables(self):
        """Generator that returns table names from the database file."""
        for table_name in self.inspection_engine.get_table_names():
            yield table_name

    def find_database_column(self, table, column):
        """Looks for a column from the database file."""
        for engine_column in self.inspection_engine.get_columns(table):
            if engine_column['name'] == column.key:
                return engine_column

    @property
    def is_sane(self):
        """Returns a boolean value that indicates whether the database file
        passes the sanity checks or not based on the length of the error list.
        """
        return not len(self.errors)

    @property
    def model_tables(self):
        """Generator that returns tuples containing model name and model class.
        Models with classes inherited from _ModuleMarker class are skipped as
        they are not actual models.
        """
        for name, class_ in self.base._decl_class_registry.items():
            if isinstance(class_, _ModuleMarker):
                continue
            yield (name, class_)

    def test(self):
        """Runs through all the database sanity tests."""
        self.test_tables()
        for table in self.database_tables:
            self.test_columns(table)
        self.test_madokami_url()  # TODO: Remove in the future.

    def test_columns(self, table):
        """Tests the columns in database table. If a column exists in the
        table, check that the column has correct datatype. If the column
        doesn't exist, add a MissingColumn object to the error list.
        """
        columns = self.inspection_engine.get_columns(table)
        column_names = [c["name"] for c in columns]

        # Search for correct class from models for the mapper.
        mapper = None
        for name, class_ in self.model_tables:
            if class_.__tablename__ == table:
                mapper = inspect(class_)
                break
        if not mapper:
            return

        for column_property in mapper.attrs:
            if isinstance(column_property, RelationshipProperty):
                # TODO: Add RelationshipProperty sanity checking.
                pass
            else:
                for column in column_property.columns:
                    if column.key in column_names:
                        self.test_datatype(table, column)
                        self.test_nullable(table, column)
                    else:
                        self.errors.append(MissingColumn(table, column.key,
                                                         parent=self))

    def test_datatype(self, table, column):
        """Tests that database column datatype matches the one defined in the
        models.
        """
        database_column = self.find_database_column(table, column)

        if isinstance(column.type, sqltypes.String):
            expected_type = sqltypes.VARCHAR
        elif isinstance(column.type, sqltypes.Integer):
            expected_type = sqltypes.INTEGER
        elif isinstance(column.type, sqltypes.Boolean):
            expected_type = sqltypes.BOOLEAN
        elif isinstance(column.type, sqltypes.DateTime):
            expected_type = sqltypes.DATETIME

        if not isinstance(database_column['type'], expected_type):
            self.errors.append(
                DatatypeMismatch(table, database_column, expected_type,
                                 parent=self)
            )

    def test_madokami_url(self):
        """Temporary function to test if Madokami series and chapters have the
        correct URL after the top-level domain change. Will be removed after an
        appropriate time has passed for people have made the switch.
        """
        global db
        from cum import db
        old_domain = 'manga.madokami.com'
        new_domain = 'manga.madokami.al'
        models = [db.Series, db.Chapter]
        for model in models:
            condition = model.url.ilike('%{}%'.format(old_domain))
            try:
                results = db.session.query(model).filter(condition).all()
            except SQLAlchemyError:
                continue
            if results:
                error = IncorrectDomain(model, old_domain, new_domain)
                self.errors.append(error)

    def test_nullable(self, table, column):
        """Tests that database column nullable status matches the one defined
        in the models.
        """
        database_column = self.find_database_column(table, column)

        if column.nullable != database_column['nullable']:
            error = NullableMismatch(table, column.key, column.nullable,
                                     parent=self)
            self.errors.append(error)

    def test_tables(self):
        """Tests if all the defined models are found in the database. If a
        table is missing, a MissingTable object is added to the error list.
        """
        for name, class_ in self.model_tables:
            table = class_.__tablename__
            if table not in self.database_tables:
                self.errors.append(MissingTable(table, parent=self))


class SanityError(metaclass=ABCMeta):
    """Base class for all sanity errors."""

    @abstractmethod
    def __str__():
        """Returns an error message that can be displayed to the user."""
        raise NotImplementedError

    @abstractmethod
    def fix(self):
        """Does appropriate changes to the database to rectify the issue."""
        raise NotImplementedError


class DatatypeMismatch(SanityError):
    """Class used for columns where the database datatype is different from the
    model datatype.
    """

    def __init__(self, table, column, expected_type, parent=None):
        self.column = column
        self.expected_type = expected_type
        self.parent = parent
        self.table = table

    def __str__(self):
        return ("{}.{} column has inappropriate datatype {} (should be {})"
                .format(self.table, self.column['name'],
                        self.column['type'], self.expected_type.__name__))

    def fix(self):
        """Uses Alembic batch operations to alter the column datatype in the table.
        """
        context = MigrationContext.configure(self.parent.engine.connect())
        op = Operations(context)
        for table in self.parent.base.metadata.sorted_tables:
            if table.name == self.table:
                for column in table.columns:
                    if column.name == self.column['name']:
                        with op.batch_alter_table(table.name) as batch_op:
                            batch_op.alter_column(column.name,
                                                  type_=column.type)
                        return


class IncorrectDomain(SanityError):
    """Class used for database entries that have an outdated domain."""

    def __init__(self, model, old_domain, new_domain):
        self.model = model
        self.old_domain = old_domain
        self.new_domain = new_domain

    def __str__(self):
        return ('{s.model.__tablename__} has entries with incorrect domain '
                '({s.old_domain} -> {s.new_domain})'
                .format(s=self))

    def fix(self):
        condition = self.model.url.ilike('%{}%'.format(self.old_domain))
        results = db.session.query(self.model).filter(condition).all()
        for result in results:
            result.url = result.url.replace(self.old_domain, self.new_domain)
        db.session.commit()


class MissingColumn(SanityError):
    """Class used for columns that are missing from the database tables."""

    def __init__(self, table, name, parent=None):
        self.name = name
        self.parent = parent
        self.table = table

    def __str__(self):
        return ('{s.table}.{s.name} column is missing from database'
                .format(s=self))

    def fix(self):
        context = MigrationContext.configure(self.parent.engine.connect())
        op = Operations(context)
        for table in self.parent.base.metadata.sorted_tables:
            if table.name == self.table:
                for column in table.columns:
                    if column.name == self.name:
                        with op.batch_alter_table(table.name) as batch_op:
                            batch_op.add_column(column.copy())
                        return


class MissingTable(SanityError):
    """Class used for tables that are missing from the database file."""

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def __str__(self):
        return ('{} table is missing from database'
                .format(self.name))

    def fix(self):
        """Searches for the schema.Table object from SQLAlchemy metadata and
        creates it using the engine bind.
        """
        for table in self.parent.base.metadata.sorted_tables:
            if table.name == self.name:
                table.create(bind=self.parent.engine)
                break


class NullableMismatch(SanityError):
    """Class used for database columns where NULLABLE differs from the model.
    """

    def __init__(self, table, name, is_nullable, parent=None):
        self.table = table
        self.name = name
        self.is_nullable = is_nullable
        self.parent = parent

    def __str__(self):
        if self.is_nullable:
            msg = 'is not nullable'
        else:
            msg = 'is nullable'
        return '{s.table}.{s.name} {msg}'.format(s=self, msg=msg)

    def fix(self):
        context = MigrationContext.configure(self.parent.engine.connect())
        op = Operations(context)
        for table in self.parent.base.metadata.sorted_tables:
            if table.name == self.table:
                for column in table.columns:
                    if column.name == self.name:
                        with op.batch_alter_table(table.name) as batch_op:
                            batch_op.alter_column(column.name,
                                                  nullable=self.is_nullable)
                        return
