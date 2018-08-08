#    Copyright 2013 - 2017 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys
import yaml

from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter import generate

from reclass_tools import helpers


def render_dir(template_dir, output_dir, contexts, env_name=None):
    """Coockiecutter echancement to use several source JSON files

    :param template_dir: directory with templates to render
    :param output_dir: directory that should be created from templates
    :param context_files: list of strings, paths to YAML or JSON files
                          that provide the context variables for rendering.
                          Merge of the files usind update() into a single
                          dict is in the same order as files in the list.
    :param env_name: name for new environment that will be created
    """
    def toyaml(value, width=0, indentfirst=False):
        string = yaml.dump(value, default_flow_style=False, width=255)
        if string.splitlines():
            return (
                ' ' * width * indentfirst +
                ('\n' + ' ' * width).join(string.splitlines()) + '\n')
        else:
            return ''

    overwrite_if_exists = True

    merged_context = {}

    for fcon in contexts:
        if fcon.endswith('.yaml'):
            context = helpers.yaml_read(fcon)
        elif fcon.endswith('.json'):
            context = helpers.json_read(fcon)
        else:
            sys.exit("Error: Please use YAML or JSON files for contexts")

        merged_context = helpers.merge_nested_objects(merged_context, context)

    merged_context['toyaml'] = toyaml
    if env_name:
        if 'cookiecutter' not in merged_context:
            merged_context['cookiecutter'] = {}
        merged_context['cookiecutter']['_env_name'] = env_name

    try:
        generate.generate_files(
            repo_dir=template_dir,
            context=merged_context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir
        )

    except UndefinedVariableInTemplate as undefined_err:
        context_str = yaml.dump(
            undefined_err.context,
            default_flow_style=False,
            width=255
        )
        print('=' * 15 + ' Context: ' + '=' * 15 +
              '\n{}'.format(context_str) + '='*40)
        print('>>> {}'.format(undefined_err.message))
        sys.exit('>>> Error message: {}'.format(undefined_err.error.message))
