from pytz import timezone
from datetime import datetime
import re
import json
from pathlib import Path
import os

from trivial_status_reports import *


this_script_dir = Path(os.path.abspath(__file__)).parent
out_dir = this_script_dir / 'out'

# Setup the top-level config
# ----------------

define_config(out_dir,
	config_timezone='US/Pacific',
	config_summary_title='My Cool System',
	config_overview_section_md='''Overview
--------

This is a mock overview section.

Status
--------''')

# Create a couple test definitions
# ----------------

define_test_definition(out_dir,
	test_id='system_a.subsystem_1',
	title='A 1',
	description='''This test validates...
mlutiline
sdfsa''')

define_test_definition(out_dir,
	test_id='system_a.subsystem_2',
	title='A 2',
	description='Blah blah')

# Report some test run results
# ----------------

report_test_run(out_dir,
	test_id='system_a.subsystem_1',
	state='ERROR',
	log='Oh NOz!')

report_test_run(out_dir,
	test_id='system_a.subsystem_1',
	state='OK',
	log='''Things went just fine...
ya ya
last line''')

report_test_run(out_dir,
	test_id='system_a.subsystem_2',
	state='ERROR',
	log='Oh NOz! Here too.')

# Generate/refresh the markdown from the above json data
# ----------------

generate_markdown(out_dir)

