import sys
import os
import tempfile

from asciinema.commands.command import Command
import asciinema.asciicast as asciicast
import asciinema.asciicast.v2 as v2
import asciinema.asciicast.raw as raw
from asciinema.api import APIError


class RecordCommand(Command):

    def __init__(self, api, args, env=None):
        Command.__init__(self, args.quiet)
        self.api = api
        self.filename = args.filename
        self.rec_stdin = args.stdin
        self.command = args.command
        self.env_whitelist = args.env
        self.title = args.title
        self.assume_yes = args.yes or args.quiet
        self.idle_time_limit = args.idle_time_limit
        self.append = args.append
        self.overwrite = args.overwrite
        self.raw = args.raw
        self.recorder = raw.Recorder() if args.raw else v2.Recorder()
        self.env = env if env is not None else os.environ

    def execute(self):
        upload = False
        append = self.append

        if self.filename == "":
            if self.raw:
                self.print_error("filename required when recording in raw mode")
                return 1
            else:
                raise Exception("Filename is required. Broadcast/Upload is disabled.")

        if os.path.exists(self.filename):
            if not os.access(self.filename, os.W_OK):
                self.print_error("can't write to %s" % self.filename)
                return 1

            if os.stat(self.filename).st_size > 0 and self.overwrite:
                os.remove(self.filename)
                append = False

            elif os.stat(self.filename).st_size > 0 and not append:
                self.print_error("%s already exists, aborting" % self.filename)
                self.print_error("use --append option if you want to append to existing recording")
                return 1

        if append:
            self.print_info("appending to asciicast at %s" % self.filename)
        else:
            self.print_info("recording asciicast to %s" % self.filename)

        self.print_info("""press <ctrl-d> or type "exit" when you're done""")

        command = self.command or self.env.get('SHELL') or 'sh'
        command_env = self.env.copy()
        command_env['ASCIINEMA_REC'] = '1'
        vars = filter(None, map((lambda var: var.strip()), self.env_whitelist.split(',')))
        captured_env = {var: self.env.get(var) for var in vars}

        try:
            self.recorder.record(
                self.filename,
                append,
                command,
                command_env,
                captured_env,
                self.rec_stdin,
                self.title,
                self.idle_time_limit
            )
        except v2.LoadError:
            self.print_error("can only append to asciicast v2 format recordings")
            return 1

        self.print_info("recording finished")
        self.print_info("asciicast saved to %s" % self.filename)
        return 0


def _tmp_path():
    fd, path = tempfile.mkstemp(suffix='-ascii.cast')
    os.close(fd)
    return path
