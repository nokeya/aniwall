import os
import types

import aniwall.version as version
from gi.repository import GLib, Gio, Gtk

from aniwall.logger import logger, debuginfo
from aniwall.parser import ImageParser
from aniwall.mainwin import MainWindow
from aniwall.settings import SettingsWindow
from aniwall.dialog import AboutDialog


class Application(Gtk.Application):
	"""Main application class"""
	def __init__(self, is_local):
		super().__init__(
			application_id="com.github.worron.aniwall", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
		)
		self.is_local = is_local
		self.mainwin = None
		self.resource_path = "/com/github/worron/aniwall/"

		self.add_main_option(
			"log-level", 0, GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
			"Set log level", "LOG_LEVEL"
		)
		self.add_main_option(
			"version", ord("v"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
			"Show application version", None
		)

		self.connect("handle-local-options", self._on_handle_local_options)

	def _load_resources(self):
		"""Initialize resources"""
		logger.info("Loading resources...")

		# Set data files locations
		self.path = dict(
			data=os.path.join(os.path.abspath(os.path.dirname(__file__)), "data"),
		)
		if logger.is_debug():
			logger.debug("Data files location:\n%s", "\n".join(k + ": " + v for k, v in self.path.items()))

		# init resources
		resource_path = os.path.join(self.path["data"], "aniwall.gresource")
		resource = Gio.Resource.load(resource_path)
		# noinspection PyProtectedMember
		resource._register()

		if logger.is_debug():
			ui_resource_path = self.resource_path + "ui/"
			resource_files = "\n".join(resource.enumerate_children(ui_resource_path, Gio.ResourceLookupFlags.NONE))
			logger.debug("List of loaded resources files:\n%s" % resource_files)

		# init settings
		if self.is_local:
			schema_source = Gio.SettingsSchemaSource.new_from_directory(
				self.path["data"],
				Gio.SettingsSchemaSource.get_default(),
				False,
			)
			schema = schema_source.lookup("com.github.worron.aniwall", False)

			self.settings = Gio.Settings.new_full(schema, None, None)

			# FIXME: get child for local settings
			def get_local_child(inst, name):
				child_schema = inst.get_property("schema") + "." + name
				return Gio.Settings.new_full(schema_source.lookup(child_schema, False), None, None)

			# noinspection PyArgumentList
			self.settings.get_child = types.MethodType(get_local_child, self.settings)
		else:
			self.settings = Gio.Settings.new("com.github.worron.aniwall")

		# set initial settings on first run
		if not self.settings.get_string("export-path"):
			self.settings.set_string("export-path", os.path.expanduser("~"))

		if logger.is_debug():
			schema = self.settings.get_property("settings-schema")
			settings_list = "\n".join(k + ": " + str(self.settings.get_value(k)) for k in schema.list_keys())
			logger.debug("Current settings:\n%s", settings_list)

		logger.info("Loading resources completed")

	def _do_startup(self):
		"""Initialize application structure"""
		logger.info("Application modules initialization...")

		# set application actions
		action = Gio.SimpleAction.new("about", None)
		action.connect("activate", self.on_about)
		self.add_action(action)

		action = Gio.SimpleAction.new("quit", None)
		action.connect("activate", self.on_quit)
		self.add_action(action)

		action = Gio.SimpleAction.new("settings", None)
		action.connect("activate", self.on_settings)
		self.add_action(action)

		# init application modules
		self.parser = ImageParser(self, os.path.join(self.path["data"], "images", "test.svg"))
		self.mainwin = MainWindow(self)
		self.setwindow = SettingsWindow(self)
		self.aboutdialog = AboutDialog(self)
		self.mainwin.update_image_list()

		# set application menu
		builder = Gtk.Builder.new_from_resource(self.resource_path + "ui/menu.ui")
		self.set_app_menu(builder.get_object("app-menu"))

		logger.info("Application modules initialization complete")

		# show window
		logger.info("Application GUI startup")
		self.mainwin.gui["window"].show_all()
		self.mainwin.update_preview()

	def do_activate(self):
		if self.mainwin is None:
			logger.info("Start aniwall application")
			self._load_resources()
			self._do_startup()

		self.mainwin.gui["window"].present()

	def do_command_line(self, command_line):
		options = command_line.get_options_dict()
		if not options.contains("version"):
			self.activate()

		return 0

	def do_shutdown(self):
		logger.info("Exit aniwall application")
		if self.mainwin is not None:
			self.mainwin.save_gui_state()
		Gtk.Application.do_shutdown(self)

	# noinspection PyMethodMayBeStatic
	def _on_handle_local_options(self, _, options):
		"""GUI handler"""
		if options.contains("version"):
			print(version.get_current())
		return -1

	# noinspection PyUnusedLocal
	@debuginfo(False, False)
	def on_about(self, *args):
		"""Action handler"""
		self.aboutdialog.show()

	# noinspection PyUnusedLocal
	def on_quit(self, *args):
		"""Action handler"""
		self.quit()

	# noinspection PyUnusedLocal
	def on_settings(self, *args):
		"""Action handler"""
		self.setwindow.show()
