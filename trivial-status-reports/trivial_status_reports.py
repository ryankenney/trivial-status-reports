from pytz import timezone
from datetime import datetime
import re
import json
from pathlib import Path
import os
import glob

# Public Methods
# ----------------

def define_config(base_directory,
	config_timezone=None,
	config_summary_title=None,
	config_overview_section_md=None):
	"""
	Writes the top-level config file (config.json) for the target directory.

	:param base_directory: The base directory where the config and and all output should go.
	:param config_summary_title: The title to apply to the summary page.
	:param config_overview_section_md: An optional section to include at the top of the markdown summary page.
	"""
	base_directory = Path(base_directory)
	config = _load_config(base_directory)
	if config_timezone is not None:
		config['timezone'] = config_timezone
	if config_summary_title is not None:
		config['summary_title'] = config_summary_title
	if config_overview_section_md is not None:
		config['overview_section_md'] = config_overview_section_md
	_write_config(base_directory, config)

def define_test_definition(base_directory, test_id, title, description, timeout_secs):
	"""
	Updates/creates a test definition to the target directory. This only updates the json metadata for the test definition (not markdown).

	:param base_directory: The base directory where the config and and all output should go.
	:param test_id: A UID for the test definition. Legal chars include `[0-9a-zA-Z_-]`.
	:param title: A human-readable title.
	:param description: A detailed description. Double-linebreaks will be treated as paragraph breaks in markdown.
	:param timeout_secs: (Feature TBD.) The number of seconds with no reports before the current state of the test is set to `TIMEOUT`.
	"""
	if type(timeout_secs) != int:
		raise Exception('Invalid timeout_secs value. Must be an integer.')
	test_id = _sanitize_filesystem_path(test_id)
	test_definition = {
		"test_id": test_id,
		"title": title,
		"description": description,
		"timeout_secs": timeout_secs
	}
	target_dir = Path(base_directory) / 'tests'
	target_dir.mkdir(parents=True, exist_ok=True)
	with open(target_dir / (test_id+'.json'), 'w') as file:
		json.dump(test_definition, file, indent=1)

def report_test_run(base_directory, test_id, state, log):
	"""
	Updates/creates a test run log to the target directory. This only updates the json metadata for the run (not markdown).

	:param base_directory: The base directory where the config and and all output should go.
	:param test_id: A UID for the test definition. Legal chars include `[0-9a-zA-Z_-]`.
	:param state: Short string used to indicate status. `OK` and `FAILED` are commonly used.
	:param log: A detailed log of the test run, which will be renderd as a code-block in markdown.
	"""
	test_id = _sanitize_filesystem_path(test_id)
	# Use UTC timestamp as run_id
	run_id = datetime.now().timestamp()
	test_run = {
		"test_id": test_id,
		"run_id": run_id,
		"state": state,
		"log": log
	}
	target_dir = Path(base_directory) / 'tests' / test_id
	target_dir.mkdir(parents=True, exist_ok=True)
	with open(target_dir / (str(run_id)+'.json'), 'w') as file:
		json.dump(test_run, file, indent=1)

def generate_markdown(base_directory):
	"""
	Updates all markdown documents from the json metadata files.

	:param base_directory: The base directory where the config and and all output should go.
	"""
	config = _load_config(base_directory)
	_generate_test_run_markdown(base_directory, config)
	_generate_test_summary_markdown(base_directory, config)
	_generate_main_summary_markdown(base_directory, config)

# Internal Methods
# ----------------

def _load_config(base_directory):
	config_file = base_directory / 'config.json'
	if not config_file.exists():
		return _get_default_config()
	with open(config_file, 'r') as file:
		return json.load(file)

def _write_config(base_directory, config):
	base_directory.mkdir(parents=True, exist_ok=True)
	with open(base_directory / 'config.json', 'w') as file:
		json.dump(config, file, indent=1)

def _get_default_config():
	return {
		'timezone': 'US/Eastern',
		'summary_title': 'Status Summary',
		'overview_section_md': None
	}

def _generate_test_run_markdown(base_directory, config):
	tests_dir = Path(base_directory) / 'tests'
	tests_dir.mkdir(parents=True, exist_ok=True)
	markdown_tests_dir = Path(base_directory) / 'md/tests'
	markdown_tests_dir.mkdir(parents=True, exist_ok=True)

	for test_dir in tests_dir.iterdir():
		if not test_dir.is_dir():
			continue
		run_files_iter = test_dir.glob('*.json')
		run_files = []
		for run_file in run_files_iter:
			run_files.append(run_file)
		# NOTE: This assumes that the run_ids (floating point UTC as-strings, are sortable).
		# Alternative is to load all into memory and sort by floating point values within the json.
		run_files.sort(key=lambda file: str(file))
		for run_file in run_files:
			with open(run_file, 'r') as file:
				run = json.load(file)
			test_id = run['test_id']
			run_id = run["run_id"]
			run_time = _get_time_str(run['run_id'], config['timezone'])
			run_state = run["state"]
			markdown_lines = []
			markdown_lines.append(f'Test [{test_id}] Run [{run_id}]')
			markdown_lines.append('========')
			markdown_lines.append('')
			markdown_lines.append(f'State: `{run_state}`')
			markdown_lines.append('')
			markdown_lines.append(f'Time: `{run_time}`')
			markdown_lines.append('')
			markdown_lines.append('Log:')
			markdown_lines.append('')
			markdown_lines.append('```')
			markdown_lines.append(run['log'])
			markdown_lines.append('```')
			markdown_lines.append('')
			markdown_lines.append('')
			markdown_test_dir = markdown_tests_dir / test_id
			markdown_test_dir.mkdir(parents=True, exist_ok=True)
			with open(markdown_test_dir / (str(run_id)+'.md'), 'w') as file:
				file.write('\n'.join(markdown_lines))

def _generate_test_summary_markdown(base_directory, config):
	tests_dir = Path(base_directory) / 'tests'
	tests_dir.mkdir(parents=True, exist_ok=True)
	markdown_tests_dir = Path(base_directory) / 'md/tests'
	markdown_tests_dir.mkdir(parents=True, exist_ok=True)

	for test_file in tests_dir.glob('*.json'):
		with open(test_file, 'r') as file:
			test_def = json.load(file)

		test_id = test_def['test_id']
		test_description = test_def['description']

		markdown_lines = []
		markdown_lines.append(f'Test [{test_id}]')
		markdown_lines.append('========')
		markdown_lines.append('')
		markdown_lines.append(f'Description')
		markdown_lines.append('--------')
		markdown_lines.append('')
		markdown_lines.append(f'{test_description}')
		markdown_lines.append('')
		markdown_lines.append(f'History')
		markdown_lines.append('--------')
		markdown_lines.append('')

		test_dir = tests_dir / test_def['test_id']
		run_files = _get_run_files_for_test(test_dir)
		for run_file in run_files:
			with open(run_file, 'r') as file:
				run = json.load(file)
			test_id = run['test_id']
			run_id = run['run_id']
			run_time = _get_time_str(run['run_id'], config['timezone'])
			run_state = run['state']
			markdown_lines.append(f'* [{run_time}]({test_id}/{run_id}.md) [**{run_state}**]')

		markdown_lines.append('')
		markdown_lines.append('')
		with open(markdown_tests_dir / (str(test_id)+'.md'), 'w') as file:
			file.write('\n'.join(markdown_lines))

def _generate_main_summary_markdown(base_directory, config):
	tests_dir = Path(base_directory) / 'tests'
	tests_dir.mkdir(parents=True, exist_ok=True)

	markdown_lines = []
	markdown_lines.append(config['summary_title'])
	markdown_lines.append('========')
	markdown_lines.append('')

	if 'overview_section_md' in config:
		markdown_lines.append(config['overview_section_md'])
		markdown_lines.append('')

	test_defs = []
	for test_file in tests_dir.glob('*.json'):
		with open(test_file, 'r') as file:
			test_defs.append(json.load(file))
	test_defs.sort(key=lambda test_def: test_def['test_id'])

	for test_def in test_defs:
		test_dir = tests_dir / test_def['test_id']
		run_files = _get_run_files_for_test(test_dir)
		if len(run_files) < 1:
			continue
		with open(run_files[0], 'r') as file:
			run = json.load(file)
		test_id =  test_def['test_id']
		test_title = test_def['title']
		run_id = run['run_id']
		run_state = run['state']
		run_time = _get_time_str(run['run_id'], config['timezone'])

		markdown_lines.append(f'* [{run_state}](md/tests/{test_id}/{run_id}.md) [{test_title}](md/tests/{test_id}.md) ({run_time})')

	markdown_lines.append('')
	markdown_lines.append('')
	with open(base_directory / 'summary.md', 'w') as file:
		file.write('\n'.join(markdown_lines))

def _get_run_files_for_test(test_dir):
	run_files_iter = test_dir.glob('*.json')
	run_files = []
	for run_file in run_files_iter:
		run_files.append(run_file)
	# NOTE: This assumes that the run_ids (floating point UTC as-strings, are sortable).
	# Alternative is to load all into memory and sort by floating point values within the json.
	run_files.sort(reverse=True, key=lambda file: str(file))
	return run_files

_unsafe_filesystem_chars = re.compile(r'[^0-9a-zA-Z_\-]+')

def _sanitize_filesystem_path(path_str):
	# Prevent any special chars (safe for filesystem)
	path_str = _unsafe_filesystem_chars.sub('_', path_str)
	return path_str

def _get_time_str(timestamp_float, tz_str):
	return datetime.fromtimestamp(timestamp_float, timezone(tz_str)).strftime('%Y-%m-%d %H-%M-%S %Z')
