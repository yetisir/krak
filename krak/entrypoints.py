import subprocess
import webbrowser
import shutil

import pytest
from sphinx.ext import apidoc
from sphinx.cmd import build

from . import common, utils
from .server.rest_api.app import tables


class BuildEntryPoint(common.EntryPoint):
    name = 'build'
    description = 'Krak Server Build Tool'

    def run(self, options):
        tables.generate_sql(
            _docker_compose_file_path() / 'borehole_database' / 'tables.sql')

    def build_parser(self, parser):
        pass


class ServerEntryPoint(common.EntryPoint):
    name = 'server'
    description = 'Krak Server Orchestrator'

    actions = {
        'new': [['rm'], ['up', '--build']],
        'resume': [['up']],
        'stop': [['stop']],
    }

    def run(self, options):
        docker_compose_file_path = _docker_compose_file_path()

        try:
            for action in self.actions.get(options.action):
                subprocess.run(
                    ['docker-compose'] + action,
                    cwd=docker_compose_file_path.as_posix(),
                )
        except KeyboardInterrupt:
            subprocess.run(
                ['docker-compose', 'stop'],
                cwd=docker_compose_file_path.as_posix(),
            )

    def build_parser(self, parser):
        parser.add_argument(
            'action', default='resume', const='resume', nargs='?',
            choices=self.actions.keys())


class TestEntryPoint(common.EntryPoint):
    name = 'test'
    description = 'Krak Test Module'

    def run(self, options):
        pytest.main(
            ['-x', utils.module_root().parent.as_posix(), '--flake8'])

    def build_parser(self, parser):
        pass


class DocumentationEntryPoint(common.EntryPoint):
    name = 'docs'
    description = 'Krak Documentation Builder'

    def run(self, options):
        # define paths
        module_path = utils.module_root()
        docs_path = module_path.parent / 'docs'
        docs_source_path = docs_path / 'source'
        docs_api_path = docs_source_path / 'api'
        docs_build_path = docs_path / 'build'
        docs_index_path = docs_build_path / 'index.html'

        # clear previously generated files
        try:
            shutil.rmtree(docs_api_path)
        except FileNotFoundError:
            pass

        # build documentation
        apidoc.main([
            module_path.as_posix(), '-o', docs_api_path.as_posix(), '--force',
            '--separate', '--implicit-namespaces'])
        build.main([
            '-b', 'html', docs_source_path.as_posix(),
            docs_build_path.as_posix()])

        webbrowser.open(docs_index_path.as_posix())

    def build_parser(self, parser):
        pass


def initialize():
    return {cls.name: cls() for cls in common.EntryPoint.__subclasses__()}


def _docker_compose_file_path():
    return utils.module_root() / 'server'
