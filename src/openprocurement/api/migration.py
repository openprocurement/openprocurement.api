# -*- coding: utf-8 -*-
from openprocurement.api.constants import LOGGER
from openprocurement.api.constants import SCHEMA_VERSION, SCHEMA_DOC
from openprocurement.api.utils.print_helpers import delimited_printer
from openprocurement.api.utils.common import get_now

LOG_INFO_PRINTER = delimited_printer(LOGGER.info, '|')


def get_db_schema_version(db):
    """This method is deprecated. Don't depend on it"""
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    return schema_doc.get("version", SCHEMA_VERSION - 1)


def set_db_schema_version(db, version):
    """This method is deprecated. Don't depend on it"""
    schema_doc = db.get(SCHEMA_DOC, {"_id": SCHEMA_DOC})
    schema_doc["version"] = version
    db.save(schema_doc)


def migrate_data(registry, destination=None):
    """This method is deprecated. Don't depend on it"""
    cur_version = get_db_schema_version(registry.db)
    if cur_version == SCHEMA_VERSION:
        return cur_version
    for step in xrange(cur_version, destination or SCHEMA_VERSION):
        LOGGER.info(
            "Migrate openprocurement schema from {} to {}".format(
                step, step + 1
            ),
            extra={'MESSAGE_ID': 'migrate_data'}
        )
        migration_func = globals().get('from{}to{}'.format(step, step + 1))
        if migration_func:
            migration_func(registry)
        set_db_schema_version(registry.db, step + 1)


class MigrationConfigurationException(Exception):
    """This exception is intended to indicate some configuration flaws"""
    pass


class MigrationExecutionException(Exception):
    """This exception is intended to indicate some migration problems"""
    pass


class AliasesInfoDTO(object):
    """Holds a mapping between package name and it's aliases"""

    def __init__(self, aliases_dict):
        """Creates the AliasesInfoDTO class

        :param aliases_dict: a dictionary with following format:

            {
                "package_name_1": ["alias1", "alias2", .. "aliasN"],
                "package_name_2": ["alias1", "alias2", .. "aliasN"],
                ...
                "package_name_N": ["alias1", "alias2", .. "aliasN"],
            }

            the list with aliases could be empty.
        """
        if not isinstance(aliases_dict, dict):
            raise MigrationConfigurationException("Wrong type of aliases_dict")
        self._aliases_dict = aliases_dict

    def get_package_aliases(self, package_name):
        return self._aliases_dict.get(package_name)


class MigrationResourcesDTO(object):

    def __init__(self, db, aliases_info):

        self.db = db

        if not isinstance(aliases_info, AliasesInfoDTO):
            raise MigrationConfigurationException("Use AliasesInfoDTO class")
        self.aliases_info = aliases_info


class BaseMigrationsRunner(object):
    """Runs migration functions iteratively"""

    # must be overridden; defines max migration executed by default
    SCHEMA_VERSION = None
    # must be overridden; id of document in the db to store actual schema version
    SCHEMA_DOC = None
    # quantity of documents read per single db request
    DB_READ_LIMIT = 1024
    # approx max quantity of documents written per single db request
    DB_BULK_WRITE_THRESHOLD = 127

    def __init__(self, migration_resources):
        """
        Params:
            :param registry: app registry
            :param root_class: Root class from the traversal of some core module.
                e.g. If migration located in the lots module, provide Root class
                from the openregistry.lots.core.traversal module.
        """
        if not isinstance(migration_resources, MigrationResourcesDTO):
            raise MigrationConfigurationException("Use MigrationResourcesDTO to start the migration")
        self.resources = migration_resources
        self.name = self.__class__.__name__

    def migrate(self, steps, schema_version_max=None, schema_doc=None):
        """Run migrations

            :param steps: iterable with MigrationStep-s
            :param schema_version: maximal schema version to migrate to. For example:
                if there's migrations like <from0to1, from1to2, from2to3>, and
                schema_version_max is equal to 2, then only first two migrations
                will be executed. If it is 0, then no migrations will proceed.
                It also has priority over the SCHEMA_VERSION
            :param schema_doc: id of the document, that holds schema version
            :param check_plugins: allows to turn off plugin check on migration.
                Useful for testing.
        """
        LOG_INFO_PRINTER(self.name, 'STARTED')
        LOG_INFO_PRINTER(self.name, 'PRE-MIGRATION STATUS-----------------')

        self._target_schema_version = schema_version_max if schema_version_max is not None else self.SCHEMA_VERSION
        self._schema_doc = schema_doc if schema_doc is not None else self.SCHEMA_DOC
        # check version of db schema
        current_version = self._get_db_schema_version()

        LOG_INFO_PRINTER(self.name, 'DB schema version: {0}'.format(current_version))
        LOG_INFO_PRINTER(self.name, 'Target DB shema version: {0}'.format(self._target_schema_version))
        LOG_INFO_PRINTER(self.name, 'Schema doc name: {0}'.format(self._schema_doc))

        if current_version == SCHEMA_VERSION:
            return current_version

        steps_available = len(steps)

        LOG_INFO_PRINTER(self.name, 'Steps available to execute: {0}'.format(steps_available))

        if self._target_schema_version > steps_available:
            raise MigrationExecutionException('There is no available migration steps to complete migration')
        elif current_version > steps_available:
            raise MigrationExecutionException('Version of the DB schema is greater than our newest migration')

        target_steps = steps[current_version:self._target_schema_version]
        curr_step = current_version

        steps_to_migrate = ', '.join(self._collect_steps_names(target_steps))
        LOG_INFO_PRINTER(self.name, 'Steps to apply: {0}'.format(steps_to_migrate))
        LOG_INFO_PRINTER(self.name, 'APPLYING MIGRATION-------------------')

        for step in target_steps:
            LOG_INFO_PRINTER(self.name, step.__name__, 'STARTED')
            self._run_step(step)
            curr_step += 1
            LOG_INFO_PRINTER(self.name, 'Increasing DB version to: {0}'.format(curr_step))
            self._set_db_schema_version(curr_step)

        LOG_INFO_PRINTER(self.__class__.__name__, 'FINISHED')

    def _run_step(self, step):
        st = step(self.resources)  # init MigrationStep

        step_name = st.__class__.__name__
        LOG_INFO_PRINTER(self.name, step_name, 'SETUP')

        st.setUp()
        self._check_step_has_defined_view(st)
        LOG_INFO_PRINTER(self.name, step_name, 'Acquiring view-based generator')
        input_generator = self.resources.db.iterview(st.view, self.DB_READ_LIMIT, include_docs=True)
        migrated_documents = []  # output buffer

        for doc_row in input_generator:
            # migrate single document
            LOG_INFO_PRINTER(self.name, step_name, 'Migrating {0}'.format(doc_row.doc['_id']))
            migrated_doc = st.migrate_document(doc_row.doc)
            if migrated_doc is None:
                LOG_INFO_PRINTER(self.name, step_name, "Skipping document")
                continue
            migrated_doc['dateModified'] = get_now() # TODO: Can be extracted to separete method later
            migrated_documents.append(migrated_doc)

            # bulk write on threshold overgrow
            if len(migrated_documents) >= self.DB_BULK_WRITE_THRESHOLD:
                LOG_INFO_PRINTER(self.name, step_name, 'DB_BULK_WRITE_THRESHOLD is hit - writing to the DB')
                self.resources.db.update(migrated_documents)
                # clean output buffer
                migrated_documents = []

        # flush buffer to the DB, because threshold could be not reached
        LOG_INFO_PRINTER(self.name, step_name, 'Saving the rest of migrated documents to the DB')
        self.resources.db.update(migrated_documents)

        LOG_INFO_PRINTER(self.name, step_name, 'TEARDOWN')
        st.tearDown()

    def _get_db_schema_version(self):
        # if there isn't such document, create it
        schema_doc = self.resources.db.get(self._schema_doc, {"_id": self._schema_doc})
        # if `version` is not found - assume that db needs only the most fresh migration
        return schema_doc.get("version", self._target_schema_version - 1)

    def _set_db_schema_version(self, version):
        schema_doc = self.resources.db.get(self._schema_doc, {"_id": self._schema_doc})
        schema_doc["version"] = version
        self.resources.db.save(schema_doc)

    def _check_step_has_defined_view(self, step):
        if not hasattr(step, 'view'):
            error_template = "Migration step {0} has not defined a view for the migration"
            error_text = error_template.format(step.__class__.__name__)
            raise MigrationConfigurationException(error_text)

    def _collect_steps_names(self, steps):
        names = []
        for s in steps:
            names.append(s.__name__)

        return tuple(names)


class BaseMigrationStep(object):
    """Container for the migration step logic

    It will be executed by MigrationRunner.
    Execution scheme:

        setUp               # setups at least `view` attribute of this class. Executed once.
        <
            runner fetches documents from the DB
            based on `view` attribute of this class
        >
        migrate_document    # executed on each document in the DB, returned by `view` view
        tearDown            # executed once after the completion of all `migrate_document` calls

    """

    def __init__(self, migration_resources):
        self.resources = migration_resources

    def setUp(self):
        """Preparation before migration steps.

        After this method call this class must have `view` attribute,
        e.g. `migration_a4_interesting_objects`, without db name.
        """
        pass

    def migrate_document(self, document):
        """Migrates single document

        Must return migrated document.
        """
        pass

    def tearDown(self):
        """Post-migration stuff

        If migration-specific view was created on the setUp, here it can be
        deleted to free db resources for next migration's view indexing.
        """
        pass
