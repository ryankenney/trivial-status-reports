from pytz import timezone
from datetime import datetime
import re
import json
from pathlib import Path
import os
import glob


print (datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d_%H-%M-%S_%Z'))
print (datetime.now(timezone('utc')).strftime('%Y-%m-%d_%H-%M-%S_%Z'))
print (datetime.now(timezone('US/Eastern')).timestamp())
print (datetime.now(timezone('utc')).timestamp())
print (datetime.now().timestamp())

_unsafe_filesystem_chars = re.compile(r'[^0-9a-zA-Z_\-]+')
_multi_dot_pattern = re.compile(r'\.+')

def define_test_definition(base_directory, test_id, title, description, timeout_secs):
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

def generate_markdown(base_directory, tz):
	_generate_test_run_markdown(base_directory, tz)
	_generate_test_summary_markdown(base_directory, tz)
	_generate_main_summary_markdown(base_directory, tz)

def _generate_test_run_markdown(base_directory, tz):
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
			run_time = datetime.fromtimestamp(run['run_id'], tz).strftime('%Y-%m-%d %H-%M-%S %Z')
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

def _generate_test_summary_markdown(base_directory, tz):
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

		# TODO: De-duplicate section
		run_files_iter = test_dir.glob('*.json')
		run_files = []
		for run_file in run_files_iter:
			run_files.append(run_file)
		# NOTE: This assumes that the run_ids (floating point UTC as-strings, are sortable).
		# Alternative is to load all into memory and sort by floating point values within the json.
		run_files.sort(reverse=True, key=lambda file: str(file))

		for run_file in run_files:
			with open(run_file, 'r') as file:
				run = json.load(file)
			test_id = run['test_id']
			run_id = run['run_id']
			# TODO: De-duplicate call
			run_time = datetime.fromtimestamp(run['run_id'], tz).strftime('%Y-%m-%d %H-%M-%S %Z')
			run_state = run['state']
			markdown_lines.append(f'* [{run_time}]({test_id}/{run_id}.md) [**{run_state}**]')

		markdown_lines.append('')
		markdown_lines.append('')
		with open(markdown_tests_dir / (str(test_id)+'.md'), 'w') as file:
			file.write('\n'.join(markdown_lines))

def _generate_main_summary_markdown(base_directory, tz):
	tests_dir = Path(base_directory) / 'tests'
	tests_dir.mkdir(parents=True, exist_ok=True)

	# TODO: Support title/description config files

	markdown_lines = []
	markdown_lines.append('System Summary')
	markdown_lines.append('========')
	markdown_lines.append('')

	test_defs = []
	for test_file in tests_dir.glob('*.json'):
		with open(test_file, 'r') as file:
			test_defs.append(json.load(file))
	test_defs.sort(key=lambda test_def: test_def['test_id'])

	for test_def in test_defs:
		test_dir = tests_dir / test_def['test_id']

		# TODO: De-duplicate section
		run_files_iter = test_dir.glob('*.json')
		run_files = []
		for run_file in run_files_iter:
			run_files.append(run_file)
		# NOTE: This assumes that the run_ids (floating point UTC as-strings, are sortable).
		# Alternative is to load all into memory and sort by floating point values within the json.
		run_files.sort(reverse=True, key=lambda file: str(file))

		if len(run_files) < 1:
			continue

		with open(run_files[0], 'r') as file:
			run = json.load(file)

		test_id =  test_def['test_id']
		test_title = test_def['title']
		run_id = run['run_id']
		run_state = run['state']
		# TODO: De-duplicate call
		run_time = datetime.fromtimestamp(run['run_id'], tz).strftime('%Y-%m-%d %H-%M-%S %Z')

		markdown_lines.append(f'* [{run_state}](md/tests/{test_id}/{run_id}.md) [{test_title}](md/tests/{test_id}.md) ({run_time})')

	markdown_lines.append('')
	markdown_lines.append('')
	with open(base_directory / 'summary.md', 'w') as file:
		file.write('\n'.join(markdown_lines))

def write_update_to_markdown(test_results, base_directory, tz=timezone('US/Eastern')):
	base_directory = Path(base_directory)
	runs_directory = Path(base_directory) / 'runs'

	# Write run metadata to json
	run_id = datetime.now(tz).strftime('%Y-%m-%d_%H-%M-%S_%Z')
	_validated_and_sanitize_test_results_json(test_results)
	runs_directory.mkdir(parents=True, exist_ok=True)
	with open(runs_directory / (run_id+'.json'), 'w') as file:
		wrapped_results = {
			"run_id": run_id,
			"test_results": test_results
		}
		json.dump(wrapped_results, file, indent=1)

	# Identify the most recent runs (by filename ordering)
	run_files = glob.glob(str(runs_directory)+'/*')
	run_files.sort(reverse=True)
	run_files = run_files[0:10]
	runs = []
	for run_file in run_files:
		with open(run_file) as file:
			runs.append(json.load(file))
	# Index the runs
	runs_index = {}
	for run in runs:
		runs_index[run["run_id"]] = run
	# Identify the superset of test_ids (across runs)
	test_ids_set = set()
	for run in runs: 
		for test_result in run["test_results"]:
			test_ids_set.add(test_result["test_id"])
	test_ids = list(test_ids_set).sort()

	report_markdown_lines = []
	report_markdown_lines.append('# Status Report')
	report_markdown_lines.append('')

	header_segments = []
	header_break_segments = []
	for run in runs:
		header_segments.append(run['run_id'])
		header_break_segments.append('--')
	report_markdown_lines.append('| Test ID | Title | ' + ' | '.join(header_segments) + ' |')
	report_markdown_lines.append('|---------|-------|' + '|'.join(header_break_segments) + '|')

	print('\n'.join(report_markdown_lines))


def _validated_and_sanitize_test_results_json(test_results):
	for test_result in test_results:
		for field in ['title', 'test_id', 'description', 'state', 'logs']:
			_ensure_required_test_field(test_result, field)
		for field in ['test_id']:
			_sanitize_test_field(test_result, field)
	
def _ensure_required_test_field(test_result, field_name):
	if field_name not in test_result or test_result[field_name] == '':
		raise Exception('Invalid/missing test field "'+field_name+'"')

def _sanitize_test_field(test_result, field_name):
	# Prevent any special chars (safe for filesystem)
	test_result[field_name] = _invalid_char_pattern.sub('_', test_result[field_name])
	# Prevent "..", which can walk out of directories (safe for filesystem)
	test_result[field_name] = _multi_dot_pattern.sub('_', test_result[field_name])

def _sanitize_filesystem_path(path_str):
	# Prevent any special chars (safe for filesystem)
	path_str = _unsafe_filesystem_chars.sub('_', path_str)
	return path_str


# TODO: Remove debug
this_script_dir = Path(os.path.abspath(__file__)).parent
test_results = [{
	"test_id": "system_a__subsystem_1",
	"title": "A 1",
	"description": "This test validates...",
	"state": "FAIED",
	"logs": "..."
},{
	"test_id": "system_a__subsystem_2",
	"title": "A 2",
	"description": """This test validates...
mlut
mlutiline
sdfsa""",
	"state": "FAIED",
	"logs": "..."
}]
#write_update_to_markdown(test_results, this_script_dir / 'out')

define_test_definition(this_script_dir / 'out',
	test_id="system_a.subsystem_1",
	title="A 1",
	description="""This test validates...
mlutiline
sdfsa""",
	timeout_secs=60)

report_test_run(this_script_dir / 'out',
	test_id="system_a.subsystem_1",
	state="OK",
	log="""Things went just fine...
ya ya
last line""")

generate_markdown(this_script_dir / 'out', timezone('US/Eastern'))
