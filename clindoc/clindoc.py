from clingo import Control
from clingo.ast import ProgramBuilder, parse_files
from sphinx.application import Sphinx
from typing import List, Dict

from .astprogram import ASTProgram, Constraint
from .builder import Builder
from .utils import create_dir, get_dir_path

import os
import shutil
import json


class Clindoc:

    """
    parameters : Parameters for the different part of the app, inc. components, sphinx...
    """

    version = "0.2.0"

    def __init__(self, parameters: Dict = {}) -> None:
        # Change paths to absolute paths, set default values ...
        self.parameters = self._check_parameters(parameters)

    def _check_parameters(self, parameters: Dict):

        if 'conf_path' in parameters:
            if parameters['conf_path']:
                with open(parameters['conf_path'], 'r') as file:
                    parameters = json.loads(file.read())
        else:
            parameters['conf_path'] = None

        if not parameters.get('src_dir'):
            parameters['src_dir'] = '.'
            
        if not parameters.get('project_name'):
            parameters['project_name'] = 'Default Name'

        parameters['src_dir'] = get_dir_path(parameters['src_dir'])

        if not parameters.get('doc_dir'):
            parameters['doc_dir'] = os.path.join(
                parameters['src_dir'], 'docs')
            
        else:
            parameters['doc_dir'] = get_dir_path(parameters['doc_dir'])

        if not parameters.get('out_dir'):
            parameters['out_dir'] = os.path.join(parameters['src_dir'], 'docs', 'build')

        if not 'builder' in parameters:
            parameters['builder'] = "html"  # Default value

        if not 'clean' in parameters:
            parameters['clean'] = False

        if not 'no_sphinx_build' in parameters:
            parameters['no_sphinx_build'] = False

        if not 'no_rst_build' in parameters:
            parameters['no_rst_build'] = False

        if not 'description' in parameters:
            parameters['description'] = 'Default description'

        if not 'conf_path' in parameters:
            parameters['conf_path'] = None
        else:
            if parameters['conf_path']:
                parameters['conf_path'] = os.path.abspath(parameters['conf_path'])

        if not 'dump_conf' in parameters:
            parameters['dump_conf'] = None
        else:
            if parameters['dump_conf']:
                parameters['dump_conf'] = os.path.abspath(parameters['dump_conf'])
        return parameters

    def _load_folder(self) -> List[ASTProgram]:
        path = self.parameters['src_dir']
        ret = []
        if not os.path.isdir(path) or not os.path.exists(path):
            raise ValueError(f"{path} is not a valid directory.")
        lp_files = []
        for root, dirs, files in os.walk(path):
            lp_files.extend([os.path.join(root, f)
                            for f in files if f.endswith(".lp")])

        for lp_file in lp_files:
            ret.append(self._load_file(lp_file))

        return ret

    def _load_file(self, path):
        Constraint.id = 0
        ctl = Control()
        with open(path) as f:
            file_lines = f.readlines()

        ast_list = []
        with ProgramBuilder(ctl) as _:
            parse_files([path], ast_list.append)

        return ASTProgram(ast_list, file_lines, path,self.parameters)

    def build_documentation(self) -> None:
        self.astprograms: List[ASTProgram] = self._load_folder()
        
        if len(self.astprograms) == 0:
            raise ValueError(f'Empty {self.parameters["src_dir"]} folder')

        if self.parameters['clean']:
            if os.path.exists(self.parameters['doc_dir']):
                shutil.rmtree(self.parameters['doc_dir'])


            if os.path.exists(self.parameters['out_dir']):
                shutil.rmtree(self.parameters['out_dir'])


        create_dir(self.parameters['doc_dir'])

        self.builder = Builder(self.astprograms, self.parameters)

        if not self.parameters['no_rst_build']:
            self.builder.build()

        if self.parameters['dump_conf']:
            with open(self.parameters['dump_conf'], 'w') as file:
                file.write(json.dumps(self.parameters, indent=4))


        self._sphinx_config = {
            "project": self.parameters['project_name'],
            "html_theme": "sphinx_rtd_theme",
            'intersphinx_mapping': {
                'python': ('https://docs.python.org/3/', None),
                'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
            },
            'extensions': [
                "sphinx.ext.napoleon",
                'sphinx.ext.intersphinx'
            ]
        }
        if not self.parameters.get('no_sphinx_build'):
            s = Sphinx(self.parameters['doc_dir'],
                       confdir=None,
                       outdir=self.parameters['out_dir'],
                       doctreedir=os.path.join(
                self.parameters['out_dir'], "pickle"),
                buildername=self.parameters['builder'],
                confoverrides=self._sphinx_config,
                verbosity=1)
            s.build()
