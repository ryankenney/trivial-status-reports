from pytz import timezone
from datetime import datetime
import re
import json
from pathlib import Path
import os

from trivial_status_reports import *

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

out_dir = this_script_dir / 'out'
define_config(out_dir,
	config_timezone='US/Pacific',
	config_summary_title="My Cool System",
	config_overview_section_md="""Overview
--------

This is a mock overview section.

Status
--------""")
generate_markdown(out_dir)
