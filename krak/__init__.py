import subprocess
import webbrowser

import pytest
from sphinx.ext import apidoc
from sphinx.cmd import build

from . import common, utils


__description__ = 'Data Collection and Management Framework'
__url__ = 'https://gihub.com/yetisir/krak'
__version__ = '0.0.1'
__author__ = ['M. Yetisir', 'P. Matlashewski']
__email__ = ''
__license__ = 'GNU GPL v 3.0'


class ServerEntryPoint(common.EntryPoint):
    name = 'server'
    description = 'Krak Server Orchestrator'

    def run(self, options):
        docker_compose_file_path = utils.module_root() / 'server'
        try:
            subprocess.run(
                ['docker-compose', 'up'],
                cwd=docker_compose_file_path.as_posix(),
            )
        except KeyboardInterrupt:
            subprocess.run(
                ['docker-compose', 'stop'],
                cwd=docker_compose_file_path.as_posix(),
            )

    def build_parser(self, parser):
        pass


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
        # create_output_directory

        module_path = utils.module_root()
        docs_path = module_path.parent / 'docs'
        docs_source_path = docs_path / 'source'
        docs_api_path = docs_source_path / 'api'
        docs_build_path = docs_path / 'build'
        docs_index_path = docs_build_path / 'index.html'
        apidoc.main([
            module_path.as_posix(), '-o', docs_api_path.as_posix(), '--force',
            '--separate'])
        build.main([
            '-b', 'html', docs_source_path.as_posix(),
            docs_build_path.as_posix()])

        webbrowser.open(docs_index_path.as_posix())
        # run apidoc
        # build sphinx
        # open docs

    def build_parser(self, parser):
        pass
