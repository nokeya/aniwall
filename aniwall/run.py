#!/usr/bin/python3

import re
import os
import sys
import gi
import signal

# check gi version
gi.require_version('Gtk', '3.0')

# set module for local run
is_local = __name__ == "__main__"
if is_local:
	sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# TODO: proper signal handling
signal.signal(signal.SIGINT, signal.SIG_DFL)


def set_log_level(args):
	# noinspection PyPep8
	from aniwall.logger import logger

	level = re.search("log-level=(\w+)", str(args))
	try:
		logger.setLevel(level.group(1))
	except Exception:
		logger.setLevel("WARNING")


def run():
	set_log_level(sys.argv)

	# noinspection PyPep8
	from aniwall.application import Application

	app = Application(is_local)
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)


if __name__ == "__main__":
	run()
