# Copyright 2015 UnitedStack, Inc.
# All Rights Reserved.
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

import os
import re
import time
import tempfile
import signal
import shlex
import subprocess
import platform
from threading import Timer
from stetho.agent.common import resource
from stetho.agent.common import log

LOG = log.get_logger()


def execute(cmd, shell=False, root=False, timeout=10):
    try:
        exec_cmd = ["sudo"] + cmd if root else list(cmd)
        LOG.info(exec_cmd)
        subproc = subprocess.Popen(
            exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell
        )
        timer = Timer(timeout, lambda proc: proc.kill(), [subproc])
        timer.start()
        subproc.wait()
        stdcode = subproc.returncode
        stdout = subproc.stdout.readlines()
        stderr = subproc.stderr.readlines()
        timer.cancel()

        def list_strip(lines):
            return [line.strip().decode("utf-8", errors="ignore") for line in lines]

        return stdcode, list_strip(stderr) if stdcode else list_strip(stdout)
    except Exception as e:
        LOG.error(str(e))
        raise


def execute_wait(cmd, shell=False, root=False):
    exec_cmd = ["sudo"] + cmd if root else list(cmd)
    subproc = subprocess.Popen(
        exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell
    )
    stdout, stderr = subproc.communicate()
    stdcode = subproc.returncode
    return (
        stdcode,
        stdout.decode("utf-8", errors="ignore"),
        stderr.decode("utf-8", errors="ignore"),
    )


def create_daemon(cmd, shell=False, root=False):
    try:
        exec_cmd = ["sudo"] + cmd if root else list(cmd)
        LOG.info(exec_cmd)
        subproc = subprocess.Popen(
            exec_cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return subproc.pid
    except Exception as e:
        LOG.error(str(e))
        raise


def kill_process_by_id(pid):
    pid = int(pid)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        os.waitpid(pid, 0)
    except OSError:
        pass


def get_linux_distribution():
    try:
        import distro

        return distro.linux_distribution()
    except ImportError:
        pass
    try:
        release = platform.release()
        return ("centos", release, "")
    except Exception:
        return ("unknown", "0.0", "")


def get_interface(interface):
    supported_dists = ["7.0", "6.5"]

    def format_centos_7_0(inf):
        pattern = r"<([A-Z]+)"
        state = re.search(pattern, stdout[0]).groups()[0]
        state = "UP" if state == "UP" else "DOWN"
        inf.state = state
        stdout.pop(0)
        pattern = r"inet\s(.*)\s\snetmask\s(.*)\s\sbroadcast\s(.*)"
        for line in stdout:
            if line.startswith("inet "):
                tmp = re.search(pattern, line).groups()
                inf.inet, inf.netmask, inf.broadcast = tmp
                stdout.remove(line)
                break
        for line in stdout:
            if line.startswith("ether"):
                inf.ether = line[6:23]
                break
        return stdcode, "", inf.make_dict()

    def format_centos_6_5(inf):
        pattern = r"HWaddr\s(.*)"
        inf.ether = re.search(pattern, stdout[0]).groups()[0]
        stdout.pop(0)
        pattern = r"addr:(.*)\s\sBcast:(.*)\s\sMask:(.*)"
        for line in stdout:
            if line.startswith("inet "):
                tmp = re.search(pattern, line).groups()
                inf.inet, inf.broadcast, inf.netmask = tmp
                stdout.remove(line)
                break
        inf.state = "DOWN"
        for line in stdout:
            if "RUNNING" in line:
                state = line[:2]
                state = "UP" if state == "UP" else "DOWN"
                inf.state = state
                break
        return stdcode, "", inf.make_dict()

    linux_dist = get_linux_distribution()[1][:3]
    if linux_dist in supported_dists:
        stdcode = 1
        stdout = None
        try:
            cmd = ["ifconfig", interface]
            stdcode, stdout = execute(cmd)
            if stdcode != 0:
                message = stdout[0] if stdout else "ifconfig command failed"
                return stdcode, message, None
            inf = resource.Interface(interface)
            if linux_dist == "6.5":
                return format_centos_6_5(inf)
            elif linux_dist == "7.0":
                return format_centos_7_0(inf)
        except Exception as e:
            message = stdout[0] if stdout else str(e)
            return stdcode, message, None

    message = "Unsupported OS distribute %s, only support for CentOS %s."
    message = message % (linux_dist, str(supported_dists))
    return 1, message, None


def register_api(server, api_obj):
    methods = dir(api_obj)
    apis = list(filter(lambda m: not m.startswith("_"), methods))
    for api in apis:
        server.register_function(getattr(api_obj, api))
    LOG.info("Registered api %s" % apis)


def make_response(code=0, message="", data=None):
    response = dict()
    response["code"] = code
    response["message"] = "" if message is None else message
    response["data"] = dict() if data is None else data
    return response


def replace_file(file_name, mode=0o644):
    base_dir = os.path.dirname(os.path.abspath(file_name))
    tmp_file = tempfile.NamedTemporaryFile("w+", dir=base_dir, delete=False)
    os.chmod(tmp_file.name, mode)
    os.rename(tmp_file.name, file_name)
