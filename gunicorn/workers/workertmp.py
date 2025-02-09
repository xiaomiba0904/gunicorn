# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import platform
import tempfile
import time

from gunicorn import util

PLATFORM = platform.system()
IS_CYGWIN = PLATFORM.startswith('CYGWIN')


class WorkerTmp(object):

    def __init__(self, cfg):
        old_umask = os.umask(cfg.umask)
        fdir = cfg.worker_tmp_dir
        if fdir and not os.path.isdir(fdir):
            raise RuntimeError("%s doesn't exist. Can't create workertmp." % fdir)
        fd, name = tempfile.mkstemp(prefix="wgunicorn-", dir=fdir)
        os.umask(old_umask)

        # change the owner and group of the file if the worker will run as
        # a different user or group, so that the worker can modify the file
        if cfg.uid != os.geteuid() or cfg.gid != os.getegid():
            util.chown(name, cfg.uid, cfg.gid)

        # unlink the file so we don't leak tempory files
        try:
            if not IS_CYGWIN:
                util.unlink(name)

            self._tmp = os.fdopen(fd, 'w+')
            self._tmp.write(str(int(time.monotonic())))
        except Exception:
            os.close(fd)
            raise

        self.spinner = 0

    def notify(self):
        self._tmp.seek(0, 0)
        self._tmp.truncate()
        self._tmp.write(str(int(time.monotonic())))

    def last_update(self):
        self._tmp.seek(0, 0)
        time_content = self._tmp.read()
        if time_content:
            return int(time_content)

        return int(time.monotonic())

    def fileno(self):
        return self._tmp.fileno()

    def close(self):
        return self._tmp.close()
