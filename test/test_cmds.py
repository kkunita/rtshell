#!/usr/bin/env python
# -*- Python -*-
# -*- coding: utf-8 -*-

'''rtshell

Copyright (C) 2009-2010
    Geoffrey Biggs
    RT-Synthesis Research Group
    Intelligent Systems Research Institute,
    National Institute of Advanced Industrial Science and Technology (AIST),
    Japan
    All rights reserved.
Licensed under the Eclipse Public License -v 1.0 (EPL)
http://www.opensource.org/licenses/eclipse-1.0.txt

Tests for the commands.

'''


import os
import os.path
import re
import rtsprofile.rts_profile
import subprocess
import sys
import tempfile
import time
import unittest


COMP_LIB_PATH='/usr/local/share/OpenRTM-aist/examples/rtcs'


class RTCLaunchFailedError(Exception):
    pass


def load_file(fn):
    with open(fn, 'r') as f:
        return f.read()

def call_process(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    output = p.communicate()
    output = (output[0].strip(), output[1].strip())
    return_code = p.returncode
    return output[0], output[1], return_code


def start_process(args):
    return subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)


def find_omninames():
    # If on Windows, ...
    # Else use ps
    procs, stderr, ret_code = call_process(['ps', '-e'])
    for p in procs.split('\n'):
        if 'omniNames' in p:
            return p.split()[0]
    return None


def launch_comp(name):
    p = subprocess.Popen([os.path.join('./test', name),
        '-f', './test/rtc.conf'], stdout=subprocess.PIPE)
    p.poll()
    if p.returncode is not None:
        raise RTCLaunchFailedError
    return p


def stop_comp(p):
    p.terminate()
    p.wait()


def start_ns():
    # Check if omniNames is running
    pid = find_omninames()
    if pid:
        # Return none to indicate the name server is not under our control
        return None
    else:
        # Start omniNames and return the PID
        return start_process('rtm-naming')


def stop_ns(p):
    if p:
        call_process(['killall', 'omniNames'])


def wait_for_comp(comp, state='Inactive', tries=40, res=0.01):
    while tries > 0:
        stdout, stderr, ret = call_process(['./rtls', '-l',
            os.path.join('/localhost/local.host_cxt', comp)])
        if stdout != '':
            if stdout.split()[0] == state:
                return
        tries -= 1
        time.sleep(res)
    raise RTCLaunchFailedError


def make_zombie(comp='zombie_comp'):
    c = launch_comp(comp)
    wait_for_comp('Zombie0.rtc')
    c.kill()
    c.wait()


def clean_zombies():
    call_process(['./rtdel', '-z'])


def launch_manager(tries=40, res=0.01):
    p = start_process(['rtcd', '-d', '-f', './test/rtc.conf'])
    while tries > 0:
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/manager.mgr'])
        if stdout == '' and stderr == '':
            return p
        tries -= 1
        time.sleep(res)
    raise RTCLaunchFailedError


def stop_manager(mgr):
    mgr.terminate()
    mgr.wait()


def add_obj_strs(args, obj1=None, obj2=None):
    if obj1 is not None:
        args.append('/localhost/local.host_cxt/{0}'.format(obj1))
    if obj2 is not None:
        args.append('/localhost/local.host_cxt/{0}'.format(obj2))
    return args


def test_notacomp(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: Not a component: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj1))
    tester.assertEqual(ret, 1)


def test_notacomp2(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: Not a component: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj2))
    tester.assertEqual(ret, 1)


def test_noobject(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: No such object: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj1))
    tester.assertEqual(ret, 1)


def test_noobject2(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: No such object: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj2))
    tester.assertEqual(ret, 1)


def test_zombie(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: Zombie object: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj1))
    tester.assertEqual(ret, 1)


def test_portnotfound(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: Port not found: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj1))
    tester.assertEqual(ret, 1)


def test_port2notfound(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: Port not found: /localhost/local.host_cxt/{1}'.format(
            os.path.basename(cmd), obj2))
    tester.assertEqual(ret, 1)


def test_sourceportnotfound(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: No source port specified.'.format(os.path.basename(cmd)))
    tester.assertEqual(ret, 1)


def test_destportnotfound(tester, cmd, obj1=None, obj2=None, extra_opts=[]):
    stdout, stderr, ret = call_process(add_obj_strs(['./{0}'.format(cmd)],
        obj1=obj1, obj2=obj2) + extra_opts)
    tester.assertEqual(stdout, '')
    tester.assertEqual(stderr,
        '{0}: No destination port specified.'.format(os.path.basename(cmd)))
    tester.assertEqual(ret, 1)


class rtactTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_success(self):
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
            'rtact: Not a component: /localhost/local.host_cxt')
        self.assertEqual(ret, 1)

    def test_manager(self):
        test_notacomp(self, './rtact', obj1='manager.mgr')

    def test_port(self):
        test_notacomp(self, './rtact', obj1='Std0.rtc:in')

    def test_trailing_slash(self):
        test_notacomp(self, './rtact', obj1='Std0.rtc/')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')

    def test_no_object(self):
        test_noobject(self, './rtact', obj1='NotAComp0.rtc')

    def test_zombie_object(self):
        test_zombie(self, './rtact', obj1='Zombie0.rtc')

    def test_no_arg(self):
        stdout, stderr, ret = call_process('./rtact')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtact: No component specified.')
        self.assertEqual(ret, 1)


def rtact_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtactTests)


class rtcatTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtcat: No such object: '
            '/localhost/local.host_cxt')
        self.assertEqual(ret, 1)

    def test_no_object(self):
        test_noobject(self, './rtcat', obj1='NotAComp0.rtc')

    def test_no_object_port(self):
        test_noobject(self, './rtcat', obj1='NotAComp0.rtc:notaport')

    def test_no_arg(self):
        stdout, stderr, ret = call_process('./rtcat')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtcat: Cannot cat a directory.')
        self.assertEqual(ret, 1)

    def test_rtc(self):
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assert_(stdout.startswith('Std0.rtc'))
        self.assert_('Inactive' in stdout)
        self.assert_('Category' in stdout)
        self.assert_('Execution Context' in stdout)
        self.assert_('DataInPort: in' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_manager(self):
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/manager.mgr'])
        self.assert_(stdout.startswith('Name: manager'))
        self.assert_('Modules:' in stdout)
        self.assert_('Loaded modules:' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_port(self):
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '+DataInPort: in')
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_(stdout.startswith('-DataInPort: in'))
        self.assert_('dataport.data_type' in stdout)
        self.assert_('TimedLong' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_port_not_rtc(self):
        test_notacomp(self, './rtcat', obj1='manager.mgr:in')

    def test_port_trailing_slash(self):
        test_noobject(self, './rtcat', obj1='Std0.rtc:in/')

    def test_bad_port(self):
        test_portnotfound(self, './rtcat', obj1='Std0.rtc:out')

    def test_rtc_trailing_slash(self):
        test_noobject(self, './rtcat', obj1='Std0.rtc/')

    def test_zombie_object(self):
        test_zombie(self, './rtcat', obj1='Zombie0.rtc')


def rtcat_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtcatTests)


class rtcheckTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        stop_ns(self._ns)

    def test_noprobs(self):
        call_process(['./rtresurrect', './test/sys.rtsys'])
        call_process(['./rtstart', './test/sys.rtsys'])
        stdout, stderr, ret = call_process(['./rtcheck', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_not_activated(self):
        call_process(['./rtresurrect', './test/sys.rtsys'])
        call_process(['./rtstart', './test/sys.rtsys'])
        call_process(['./rtdeact', '/localhost/local.host_cxt/Std0.rtc'])
        wait_for_comp('Std0.rtc', state='Inactive')
        stdout, stderr, ret = call_process(['./rtcheck', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
                'Component /localhost/local.host_cxt/Std0.rtc '\
                'is in incorrect state Inactive')
        self.assertEqual(ret, 1)

    def test_not_connected(self):
        call_process(['./rtresurrect', './test/sys.rtsys'])
        call_process(['./rtstart', './test/sys.rtsys'])
        call_process(['./rtdis', '/localhost/local.host_cxt/Std0.rtc'])
        stdout, stderr, ret = call_process(['./rtcheck', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'No connection between '\
                '/localhost/local.host_cxt/Output0.rtc:out and '\
                '/localhost/local.host_cxt/Std0.rtc:in')
        self.assertEqual(ret, 1)


def rtcheck_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtcheckTests)


class rtcompTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._mgr = launch_manager()
        self._load_mgr()

    def tearDown(self):
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def _load_mgr(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Controller.so'), '-i',
            'ControllerInit', '-c', 'Controller'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Sensor.so'), '-i',
            'SensorInit', '-c', 'Sensor'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Motor.so'), '-i',
            'MotorInit', '-c', 'Motor'])
        self.assertEqual(ret, 0)

    def test_success(self):
        stdout, stderr, ret = call_process(['./rtcomp',
            '/localhost/local.host_cxt/manager.mgr', '-c',
            '/localhost/local.host_cxt/Controller0.rtc', '-p',
            '/localhost/local.host_cxt/Sensor0.rtc:in', '-p',
            '/localhost/local.host_cxt/Motor0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._assert_comp_exists('CompositeRTC.rtc')

    def test_set_name(self):
        stdout, stderr, ret = call_process(['./rtcomp',
            '/localhost/local.host_cxt/manager.mgr', '-c',
            '/localhost/local.host_cxt/Controller0.rtc', '-p',
            '/localhost/local.host_cxt/Sensor0.rtc:in', '-p',
            '/localhost/local.host_cxt/Motor0.rtc:out', '-n',
            'Blurgle'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._assert_comp_exists('Blurgle.rtc')

    def _assert_comp_exists(self, name):
        wait_for_comp(name)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/{0}'.format(name)])
        self.assertEqual(stdout, name)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)


def rtcomp_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtcompTests)


class rtconTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        self._err = launch_comp('err_comp')
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')
        wait_for_comp('Err0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        stop_comp(self._err)
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_connect(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' in stdout)

    def test_set_props(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-p', 'dataport.subscription_type=new'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('dataport.subscription_type      new' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('dataport.subscription_type      new' in stdout)

    def test_bad_prop(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-p', 'dataport.subscription_type'])
        self.assertEqual(stdout, '')
        self.assert_(
            'Bad property format: dataport.subscription_type' in stderr)
        self.assertEqual(ret, 2)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('Connected to: /localhost/local.host_cxt/Output0.rtc:out'\
                not in stdout)

    def test_set_name(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-n', 'test_conn'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('test_conn' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('test_conn' in stdout)

    def test_set_id(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-i', 'conn_id'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('conn_id' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-ll',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('conn_id' in stdout)

    def test_no_source_port(self):
        test_sourceportnotfound(self, './rtcon', obj1='Std0.rtc',
                obj2='Output0.rtc:out')
        test_sourceportnotfound(self, './rtcon', obj1='Output0.rtc',
                obj2='Std0.rtc:in')

    def test_not_enough_targets(self):
        stdout, stderr, ret = call_process(['./rtcon', 'Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assert_('Usage:' in stderr)
        self.assertEqual(ret, 1)

    def test_too_many_targets(self):
        stdout, stderr, ret = call_process(['./rtcon', 'Std0.rtc:in',
            'Output0.rtc:out', 'Err0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assert_('Usage:' in stderr)
        self.assertEqual(ret, 1)

    def test_no_dest_port(self):
        test_destportnotfound(self, './rtcon', obj1='Std0.rtc:in',
                obj2='Output0.rtc')
        test_destportnotfound(self, './rtcon', obj1='Output0.rtc:out',
                obj2='Std0.rtc')

    def test_bad_source_port(self):
        test_portnotfound(self, './rtcon', obj1='Std0.rtc:noport',
                obj2='Output0.rtc:out')
        test_portnotfound(self, './rtcon', obj1='Output0.rtc:noport',
                obj2='Std0.rtc:in')

    def test_bad_source_rtc(self):
        test_noobject(self, './rtcon', obj1='NotAComp0.rtc:in',
                obj2='Output0.rtc:out')
        test_noobject(self, './rtcon',
                obj1='NotAComp0.rtc:out',
                obj2='Std0.rtc:in')

    def test_bad_dest_port(self):
        test_port2notfound(self, './rtcon', obj1='Std0.rtc:in',
                obj2='Output0.rtc:noport')
        test_port2notfound(self, './rtcon', obj1='Output0.rtc:out',
                obj2='Std0.rtc:noport')

    def test_bad_dest_rtc(self):
        test_noobject2(self, './rtcon', obj1='Std0.rtc:in',
                obj2='NotAComp0.rtc:out')
        test_noobject2(self, './rtcon', obj1='Output0.rtc:out',
                obj2='NotAComp0.rtc:in')

    def test_bad_polarity(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtcon: Wrong port type.')
        self.assertEqual(ret, 1)

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt:port',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
            'rtcon: Not a component: /localhost/local.host_cxt:port')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt:port'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
            'rtcon: Not a component: /localhost/local.host_cxt:port')
        self.assertEqual(ret, 1)

    def test_manager(self):
        test_sourceportnotfound(self, './rtcon', obj1='manager.mgr',
            obj2='Output0.rtc:out')
        test_destportnotfound(self, './rtcon', obj1='Std0.rtc:in', obj2='manager.mgr')
        test_notacomp(self, './rtcon', obj1='manager.mgr:port',
            obj2='Output0.rtc:out')
        test_notacomp2(self, './rtcon', obj1='Std0.rtc:in',
                obj2='manager.mgr:port')


def rtcon_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtconTests)


class rtconfTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_ns(self._ns)

    def test_list(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'list'])
        self.assert_('+default*' in stdout)
        self.assert_('+set1' in stdout)
        self.assert_('+set2' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_list_long(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'list', '-l'])
        self.assertEqual(stdout,
                '-default*\n  param  0\n'\
                '-set1\n  param  1\n'\
                '-set2\n  param  2')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_list_hidden_set_error(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '/localhost/local.host_cxt/Std0.rtc', 'list'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: __hidden__')
        self.assertEqual(ret, 1)

    def test_list_hidden_set_ok(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '-a', '/localhost/local.host_cxt/Std0.rtc', 'list'])
        self.assertEqual(stdout, '+__hidden__')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_list_bad_set(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'noset',
            '/localhost/local.host_cxt/Std0.rtc', 'list'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: noset')
        self.assertEqual(ret, 1)

    def test_set_default(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'set', 'param', '42'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '42')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set1',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '1')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '2')

    def test_set_other(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set1',
            '/localhost/local.host_cxt/Std0.rtc', 'set', 'param', '42'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'default',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '0')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set1',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '42')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '2')

    def test_set_hidden_error(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '/localhost/local.host_cxt/Std0.rtc', 'set', 'param', '42'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: __hidden__')
        self.assertEqual(ret, 1)

    def test_set_hidden_ok(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '-a', '/localhost/local.host_cxt/Std0.rtc', 'set', 'param', '42'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '-a', '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '42')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'default',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '0')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set1',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '1')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '2')

    def test_get_default(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '0')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_get_other(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '2')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_get_bad_set(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'noset',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: noset')
        self.assertEqual(ret, 1)

    def test_get_bad_param(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'noparam'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
                'rtconf: No such configuration parameter: noparam')
        self.assertEqual(ret, 1)

    def test_get_hidden_error(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: __hidden__')
        self.assertEqual(ret, 1)

    def test_get_hidden_ok(self):
        stdout, stderr, ret = call_process(['./rtconf', '-s', '__hidden__',
            '-a', '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '3')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_act(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'act', 'set1'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'list'])
        self.assertEqual(stdout, '+default\n+set1*\n+set2')

    def test_act_bad_set(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'act', 'noset'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: noset')
        self.assertEqual(ret, 1)

    def test_act_hidden_error(self):
        stdout, stderr, ret = call_process(['./rtconf',
            '/localhost/local.host_cxt/Std0.rtc', 'act', '__hidden__'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtconf: No such configuration set: __hidden__')
        self.assertEqual(ret, 1)

    def test_act_hidden_ok(self):
        stdout, stderr, ret = call_process(['./rtconf', '-a',
            '/localhost/local.host_cxt/Std0.rtc', 'act', '__hidden__'])
        self.assertEqual(stdout, '')
        self.assert_('SDOPackage.InternalError' in stderr)
        self.assertEqual(ret, 1)

    def test_context(self):
        test_noobject(self, './rtconf', obj1='')

    def test_manager(self):
        test_noobject(self, './rtconf', obj1='manager.rtc',
                extra_opts=['list'])

    def test_port(self):
        test_notacomp(self, './rtconf', obj1='Std0.rtc:in')

    def test_trailing_slash(self):
        test_noobject(self, './rtconf', obj1='Std0.rtc/')

    def test_bad_comp(self):
        test_noobject(self, './rtconf', obj1='NotAComp0.rtc')

    def test_zombie(self):
        test_zombie(self, './rtconf', obj1='Zombie0.rtc')


def rtconf_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtconfTests)


class rtcryoTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        stop_ns(self._ns)

    def _check_rtsys_xml(self, rtsys):
        self.assert_(rtsys.startswith('<?xml'))
        # Components
        self.assert_('rts:instanceName="Std0"' in rtsys)
        self.assert_('rts:instanceName="Output0"' in rtsys)
        # Configuration sets and parameters
        self.assert_('rts:ConfigurationSets rts:id="default"' in rtsys)
        self.assert_('rts:ConfigurationSets rts:id="__hidden__"' in rtsys)
        self.assert_('rts:ConfigurationSets rts:id="set1"' in rtsys)
        self.assert_('rts:ConfigurationSets rts:id="set2"' in rtsys)
        self.assert_('rts:name="param"' in rtsys)
        self.assert_('rts:data="0"' in rtsys)
        self.assert_('rts:data="1"' in rtsys)
        self.assert_('rts:data="42"' in rtsys)
        self.assert_('rts:data="3"' in rtsys)
        # Connections
        self.assert_('rts:DataPortConnectors' in rtsys)
        self.assert_('rts:name="in_out"' in rtsys)
        self.assert_('rts:sourceDataPort' in rtsys)
        self.assert_('rts:portName="Output0.out"' in rtsys)
        self.assert_('rts:targetDataPort' in rtsys)
        self.assert_('rts:portName="Std0.in"' in rtsys)
        # Can it be loaded?
        rtsprofile.rts_profile.RtsProfile(xml_spec=rtsys)

    def _check_rtsys_yaml(self, rtsys):
        self.assert_(rtsys.startswith('rtsProfile:'))
        # Components
        self.assert_('instanceName: Std0' in rtsys)
        self.assert_('instanceName: Output0' in rtsys)
        # Configuration sets and parameters
        self.assert_('id: default' in rtsys)
        self.assert_('id: __hidden__' in rtsys)
        self.assert_('id: set1' in rtsys)
        self.assert_('id: set2' in rtsys)
        self.assert_('name: param' in rtsys)
        self.assert_("data: '0'" in rtsys)
        self.assert_("data: '1'" in rtsys)
        self.assert_("data: '42'" in rtsys)
        self.assert_("data: '3'" in rtsys)
        # Connections
        self.assert_('dataPortConnectors' in rtsys)
        self.assert_('name: in_out' in rtsys)
        self.assert_('sourceDataPort' in rtsys)
        self.assert_('portName: Output0.out' in rtsys)
        self.assert_('targetDataPort' in rtsys)
        self.assert_('portName: Std0.in' in rtsys)
        # Can it be loaded?
        rtsprofile.rts_profile.RtsProfile(yaml_spec=rtsys)

    def test_freeze_to_stdout_xml(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-x'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._check_rtsys_xml(stdout)

    def test_freeze_to_file_xml(self):
        f, fn = tempfile.mkstemp(prefix='rtshell_test_')
        os.close(f)
        stdout, stderr, ret = call_process(['./rtcryo', '-x', '-o', fn])
        rtsys = load_file(fn)
        os.remove(fn)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._check_rtsys_xml(rtsys)

    def test_freeze_to_stdout_yaml(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-y'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._check_rtsys_yaml(stdout)

    def test_freeze_to_file_yaml(self):
        f, fn = tempfile.mkstemp(prefix='rtshell_test_')
        os.close(f)
        stdout, stderr, ret = call_process(['./rtcryo', '-y', '-o', fn])
        rtsys = load_file(fn)
        os.remove(fn)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self._check_rtsys_yaml(rtsys)

    def test_freeze_abstract(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-a',
            'This is an abstract'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        orig = load_file('./test/sys.rtsys')
        self.assertNotEqual(stdout, orig)
        self.assert_('rts:abstract="This is an abstract"' in stdout)

    def test_freeze_sysname(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-n',
            'system name'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        orig = load_file('./test/sys.rtsys')
        self.assertNotEqual(stdout, orig)
        self.assert_('rts:id="RTSystem :Me.system name.0"' in stdout)

    def test_freeze_version(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-v',
            '42'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        orig = load_file('./test/sys.rtsys')
        self.assertNotEqual(stdout, orig)
        self.assert_('rts:id="RTSystem :Me.RTSystem.42"' in stdout)

    def test_freeze_vendor(self):
        stdout, stderr, ret = call_process(['./rtcryo', '-e',
            'UnitTest'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        orig = load_file('./test/sys.rtsys')
        self.assertNotEqual(stdout, orig)
        self.assert_('rts:id="RTSystem :UnitTest.RTSystem.0"' in stdout)


def rtcryo_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtcryoTests)


class rtcwdTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_cwd_nothing(self):
        stdout, stderr, ret = self._run_rtcwd('')
        self.assertEqual(stdout, 'export RTCSH_CWD="/"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_cwd_root(self):
        stdout, stderr, ret = self._run_rtcwd('/')
        self.assertEqual(stdout, 'export RTCSH_CWD="/"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_cwd_ns(self):
        stdout, stderr, ret = self._run_rtcwd('/localhost')
        self.assertEqual(stdout, 'export RTCSH_CWD="/localhost"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = self._run_rtcwd('/localhost/')
        self.assertEqual(stdout, 'export RTCSH_CWD="/localhost/"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_cwd_cxt(self):
        stdout, stderr, ret = self._run_rtcwd('/localhost/local.host_cxt')
        self.assertEqual(stdout, 'export RTCSH_CWD="/localhost/local.host_cxt"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = self._run_rtcwd('/localhost/local.host_cxt/')
        self.assertEqual(stdout, 'export RTCSH_CWD="/localhost/local.host_cxt/"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_cwd_comp(self):
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtcwd: Not a directory: '\
                '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/Std0.rtc/')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtcwd: Not a directory: '\
                '/localhost/local.host_cxt/Std0.rtc/')
        self.assertEqual(ret, 1)

    def test_cwd_mgr(self):
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/manager.mgr')
        self.assertEqual(stdout,
                'export RTCSH_CWD="/localhost/local.host_cxt/manager.mgr"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/manager.mgr/')
        self.assertEqual(stdout,
                'export RTCSH_CWD="/localhost/local.host_cxt/manager.mgr/"')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)


    def test_cwd_no_object(self):
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/Nothing')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
                'rtcwd: Not a directory: /localhost/local.host_cxt/Nothing')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = self._run_rtcwd(
                '/localhost/local.host_cxt/Nothing/')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
                'rtcwd: Not a directory: /localhost/local.host_cxt/Nothing/')
        self.assertEqual(ret, 1)


    def _run_rtcwd(self, target):
        return call_process(['python', '-c',
            'import sys; import rtshell.rtcwd; sys.exit(rtshell.rtcwd.main('\
            '["{0}"]))'.format(target)])


def rtcwd_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtcwdTests)


class rtdeactTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        call_process(['./rtact', '/localhost/local.host_cxt/Std0.rtc'])
        wait_for_comp('Std0.rtc', state='Active')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_success(self):
        stdout, stderr, ret = call_process(['./rtdeact',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtdeact',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
            'rtdeact: Not a component: /localhost/local.host_cxt')
        self.assertEqual(ret, 1)


    def test_manager(self):
        test_notacomp(self, './rtdeact', obj1='manager.mgr')

    def test_port(self):
        test_notacomp(self, './rtdeact', obj1='Std0.rtc:in')

    def test_trailing_slash(self):
        test_notacomp(self, './rtdeact', obj1='Std0.rtc/')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')

    def test_no_object(self):
        test_noobject(self, './rtdeact', obj1='NotAComp0.rtc')

    def test_zombie_object(self):
        test_zombie(self, './rtdeact', obj1='Zombie0.rtc')

    def test_no_arg(self):
        stdout, stderr, ret = call_process('./rtdeact')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdeact: No component specified.')
        self.assertEqual(ret, 1)


def rtdeact_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtdeactTests)


class rtdelTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        self._load_mgr()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def _load_mgr(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Motor.so'), '-i',
            'MotorInit', '-c', 'Motor'])
        self.assertEqual(ret, 0)

    def test_rtc(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')

    def test_manager(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/manager.mgr'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/manager.mgr'])
        self.assertEqual(stdout, '')

    def test_manager_child(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/manager.mgr/Motor0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdel: Parent not a directory: '
            '/localhost/local.host_cxt/manager.mgr/Motor0.rtc')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/manager.mgr/Motor0.rtc'])
        self.assertEqual(stdout, 'Motor0.rtc')

    def test_port(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdel: Undeletable object: '
            '/localhost/local.host_cxt/Std0.rtc:in')
        self.assertEqual(ret, 1)

    def test_ns(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdel: Undeletable object: /localhost')
        self.assertEqual(ret, 1)

    def test_trailing_slash(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/Std0.rtc/'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')

    def test_zombie(self):
        stdout, stderr, ret = call_process(['./rtdel',
            '/localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '')

    def test_notazombie(self):
        stdout, stderr, ret = call_process(['./rtdel', '-z',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdel: Not a zombie object: '
            '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, 'Std0.rtc')

    def test_isazombie(self):
        stdout, stderr, ret = call_process(['./rtdel', '-z',
            '/localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '')

    def test_all_zombies(self):
        stdout, stderr, ret = call_process(['./rtdel', '-z'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, 'Std0.rtc')
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '')


def rtdel_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtdelTests)


class rtdisTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        self._err = launch_comp('err_comp')
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')
        wait_for_comp('Err0.rtc')
        self._connect_comps()

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        stop_comp(self._err)
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def _connect_comps(self):
        stdout, stderr, ret = call_process(['./rtcon', '-i', 'con1',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcon', '-i', 'con2',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assertEqual(ret, 0)

    def test_disconnect_all(self):
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' not in stdout)
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)

    def test_disconnect_one_from_many(self):
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' not in stdout)
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' in stdout)

    def test_disconnect_one_from_one(self):
        # Get rid of one connection to prepare for the test
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(ret, 0)
        # Now test
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Err0.rtc:in',])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)

    def test_disconnect_one_by_id(self):
        stdout, stderr, ret = call_process(['./rtdis', '-i', 'con1',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' not in stdout)
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' in stdout)

    def test_disconnect_all_by_id(self):
        stdout, stderr, ret = call_process(['./rtdis', '-i', 'con1', '-v', 
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' not in stdout)
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' not in stdout)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Err0.rtc:in'])
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out' in stdout)

    def test_disconnect_not_connected(self):
        # Get rid of one connection to prepare for the test
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(ret, 0)
        # Now test
        stdout, stderr, ret = call_process(['./rtdis',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdis: No connection from '
            '/localhost/local.host_cxt/Output0.rtc:out to '
            '/localhost/local.host_cxt/Std0.rtc:in')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' in stdout)

    def test_disconnect_bad_id(self):
        stdout, stderr, ret = call_process(['./rtdis', '-i', 'no_id',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '/localhost/local.host_cxt/Std0.rtc:in',])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtdis: No connection from '
            '/localhost/local.host_cxt/Output0.rtc:out with ID no_id')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' in stdout)
        self.assert_('/localhost/local.host_cxt/Err0.rtc:in' in stdout)

    def test_no_source_port(self):
        test_sourceportnotfound(self, 'rtdis', obj1='Std0.rtc',
                obj2='Output0.rtc:out')
        test_sourceportnotfound(self, 'rtdis', obj1='Output0.rtc',
                obj2='Std0.rtc:in')

    def test_too_many_targets(self):
        stdout, stderr, ret = call_process(['./rtdis', 'Std0.rtc:in',
            'Output0.rtc:out', 'Err0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assert_('Usage:' in stderr)
        self.assertEqual(ret, 1)

    def test_no_dest_port(self):
        test_destportnotfound(self, 'rtdis', obj1='Std0.rtc:in',
                obj2='Output0.rtc')
        test_destportnotfound(self, 'rtdis', obj1='Output0.rtc:out',
                obj2='Std0.rtc')

    def test_bad_source_port(self):
        test_portnotfound(self, 'rtdis', obj1='Std0.rtc:noport',
                obj2='Output0.rtc:out')
        test_portnotfound(self, 'rtdis', obj1='Output0.rtc:noport',
                obj2='Std0.rtc:in')

    def test_bad_source_rtc(self):
        test_sourceportnotfound(self, 'rtdis', obj1='',
                obj2='Output0.rtc:out')
        test_noobject(self, 'rtdis', obj1='Std0.rtc/:in',
                obj2='Output0.rtc:out')
        test_noobject(self, 'rtdis', obj1='NotAComp0.rtc:in',
                obj2='Output0.rtc:out')
        test_noobject(self, 'rtdis',
                obj1='NotAComp0.rtc:out',
                obj2='Std0.rtc:in')

    def test_bad_dest_port(self):
        test_port2notfound(self, 'rtdis', obj1='Std0.rtc:in',
                obj2='Output0.rtc:noport')
        test_port2notfound(self, 'rtdis', obj1='Output0.rtc:out',
                obj2='Std0.rtc:noport')

    def test_bad_dest_rtc(self):
        test_noobject2(self, 'rtdis', obj1='Std0.rtc:in',
                obj2='Output0.rtc/:out')
        test_noobject2(self, 'rtdis', obj1='Std0.rtc:in',
                obj2='NotAComp0.rtc:out')
        test_noobject2(self, 'rtdis', obj1='Output0.rtc:out',
                obj2='NotAComp0.rtc:in')

    def test_context(self):
        test_noobject(self, 'rtdis', obj1=':port', obj2='Output0.rtc:out')
        test_noobject2(self, 'rtdis', obj1='Std0.rtc:in', obj2=':port')

    def test_manager(self):
        test_notacomp(self, 'rtdis', obj1='manager.mgr:port',
            obj2='Output0.rtc:out')
        test_notacomp2(self, 'rtdis', obj1='Std0.rtc:in', obj2='manager.mgr:port')


def rtdis_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtdisTests)


class rtexitTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_rtc(self):
        stdout, stderr, ret = call_process(['./rtexit',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, '*Std0.rtc')

    def test_no_args(self):
        stdout, stderr, ret = call_process(['./rtexit'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtexit: No component specified.')
        self.assertEqual(ret, 1)

    def test_context(self):
        test_notacomp(self, 'rtexit', '')

    def test_manager(self):
        test_notacomp(self, 'rtexit', obj1='manager.mgr')

    def test_port(self):
        test_notacomp(self, 'rtexit', obj1='Std0.rtc:in')

    def test_trailing_slash(self):
        test_notacomp(self, 'rtexit', obj1='Std0.rtc/')
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, 'Std0.rtc')

    def test_no_object(self):
        test_noobject(self, 'rtexit', obj1='NotAComp0.rtc')

    def test_zombie_object(self):
        test_zombie(self, 'rtexit', obj1='Zombie0.rtc')


def rtexit_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtexitTests)


class rtfindTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_find_by_exact_name(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'Std0.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_c(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'c'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc' in stdout)
        self.assert_('/localhost/local.host_cxt/Output0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_d(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'd'])
        self.assert_('/localhost' in stdout)
        self.assert_('/localhost/local.host_cxt' in stdout)
        self.assert_('/localhost/local.host_cxt/manager.mgr' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_m(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'm'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/manager.mgr')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_n(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'n'])
        self.assertEqual(stdout, '/localhost')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_z(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'z'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Zombie0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_type_multiple(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-t', 'cm'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc' in stdout)
        self.assert_('/localhost/local.host_cxt/Output0.rtc' in stdout)
        self.assert_('/localhost/local.host_cxt/manager.mgr' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_part_name(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'Std*'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', '*d0.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'Std?.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_find_by_exact_iname(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-i', 'std0.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtfind', '.', '-i', 'std0.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_max_depth(self):
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'Std0.rtc',
            '-m', '1'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtfind', '.', '-n', 'Std0.rtc',
            '-m', '3'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_prefix(self):
        stdout, stderr, ret = call_process(['./rtfind',
            '/localhost/local.host_cxt/', '-n', 'Std0.rtc'])
        self.assertEqual(stdout, '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_bad_prefix(self):
        stdout, stderr, ret = call_process(['./rtfind',
            '/localhost/local.host_cxt/Std0.rtc/', '-i', 'std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtfind: Not a directory: '
            '/localhost/local.host_cxt/Std0.rtc/')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtfind',
            '/localhost/local.host_cxt/Std0.rtc:in', '-i', 'std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtfind: Not a directory: '
            '/localhost/local.host_cxt/Std0.rtc:in')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtfind',
            '/localhost/not_a.host_cxt', '-i', 'std0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtfind: No such object: '
            '/localhost/not_a.host_cxt')
        self.assertEqual(ret, 1)


def rtfind_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtfindTests)


class rtinjectTests(unittest.TestCase):
    def setUp(self):
        self._clean_comp_output()
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._c2 = launch_comp('c2_comp')
        wait_for_comp('Std0.rtc')
        wait_for_comp('C20.rtc')
        call_process(['./rtact', '/localhost/local.host_cxt/Std0.rtc'])
        call_process(['./rtact', '/localhost/local.host_cxt/C20.rtc'])
        wait_for_comp('Std0.rtc', 'Active')
        wait_for_comp('C20.rtc', 'Active')

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._c2)
        stop_ns(self._ns)
        self._clean_comp_output()

    def _get_comp_output(self, name):
        with open(os.path.join('./test', name + '_rcvd'), 'r') as f:
            return f.read()

    def _clean_comp_output(self):
        if os.path.exists('./test/std_rcvd'):
            os.remove('./test/std_rcvd')
        if os.path.exists('./test/c2_rcvd'):
            os.remove('./test/c2_rcvd')

    def test_stdin(self):
        p = subprocess.Popen(['./rtinject',
            '/localhost/local.host_cxt/Std0.rtc:in'], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate('RTC.TimedLong({time}, 42)')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(self._get_comp_output('std'), '42\n')

    def test_option(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        time.sleep(1)
        self.assertEqual(self._get_comp_output('std'), '42\n')

    def test_max(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)', '-n', '3',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        time.sleep(1.5)
        self.assertEqual(self._get_comp_output('std'), '42\n42\n42\n')

    def test_timeout(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)', '-t', '2',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        time.sleep(3)
        comp_out = self._get_comp_output('std')
        self.assert_('42' in comp_out)
        count = len(comp_out.split('\n'))
        self.assert_(count > 1000 and count < 2000)

    def _test_rate(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)', '-t', '2', '-r', '1',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        time.sleep(3)
        comp_stdout = self._std.stdout.read()
        self.assertEqual(comp_stdout, '42\n42\n')

    def test_mod(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'MyData.Bleg(val1=4, val2=2)', '-m', 'MyData', '-p', './test',
            '/localhost/local.host_cxt/C20.rtc:input'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        time.sleep(1)
        self.assertEqual(self._get_comp_output('c2'),
                'MyData.Bleg(val1=4L, val2=2L)\n')

    def test_mod_no_path(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'MyData.Bleg(val1=4, val2=2)', '-m', 'MyData',
            '/localhost/local.host_cxt/C20.rtc:input'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtinject: No module named MyData')
        self.assertEqual(ret, 1)

    def test_bad_comp(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)',
            '/localhost/local.host_cxt/NotAComp0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtinject: No such object: '
            '/localhost/local.host_cxt/NotAComp0.rtc')
        self.assertEqual(ret, 1)

    def test_bad_port(self):
        stdout, stderr, ret = call_process(['./rtinject', '-c',
            'RTC.TimedLong({time}, 42)',
            '/localhost/local.host_cxt/Std0.rtc:out'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtinject: Port not found: '
            '/localhost/local.host_cxt/Std0.rtc:out')
        self.assertEqual(ret, 1)


def rtinject_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtinjectTests)


class rtlogTests(unittest.TestCase):
    # TODO: Add missing tests:
    # --absolute-times
    def setUp(self):
        self._clean_comp_output()
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        self._c1 = launch_comp('c1_comp')
        self._c2 = launch_comp('c2_comp')
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')
        wait_for_comp('C10.rtc')
        wait_for_comp('C20.rtc')
        call_process(['./rtact', '/localhost/local.host_cxt/Std0.rtc'])
        call_process(['./rtact', '/localhost/local.host_cxt/C20.rtc'])
        wait_for_comp('Std0.rtc', 'Active')
        wait_for_comp('C20.rtc', 'Active')

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        stop_comp(self._c1)
        stop_comp(self._c2)
        stop_ns(self._ns)

    def _get_comp_output(self, name):
        with open(os.path.join('./test', name + '_rcvd'), 'r') as f:
            return f.read()

    def _clean_comp_output(self):
        if os.path.exists('./test/std_rcvd'):
            os.remove('./test/std_rcvd')
        if os.path.exists('./test/c2_rcvd'):
            os.remove('./test/c2_rcvd')
        if os.path.exists('./test/test.rtlog'):
            os.remove('./test/test.rtlog')

    def _num_recorded(self, text):
        return int(re.search(r'Number of entries: (\d+)\n', text).groups()[0])

    def _log_start(self, text):
        return float(re.search(r'Start time: \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \((\d+.\d+)\)\n', text).groups()[0])

    def _log_end(self, text):
        return float(re.search(r'End time: \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \((\d+.\d+)\)\n', text).groups()[0])

    def test_playback(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtlog: End of log reached.')
        self.assertEqual(ret, 0)
        self.assertEqual(self._get_comp_output('std'), '0\n1\n2\n3\n4\n')

    def test_playback_from_middle_index(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-i', '-s', '2'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Playing from entry 2.\nrtlog: '
            'End of log reached.')
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '2\n3\n4\n')

    def test_playback_to_middle_index(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-i', '-e', '3'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Playing 3 entries.')
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '0\n1\n2\n')

    def test_playback_from_middle_to_middle_index(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-i', '-s', '2', '-e', '2'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Playing from entry 2 to entry 2.')
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '2\n')

    def test_playback_from_middle_time(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-s', '1292489688'])
        self.assertEqual(stdout, '')
        self.assert_(re.match(r'Playing from \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \(\d+.\d+\)\.\nrtlog: End of log reached.',
            stderr) is not None)
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '1\n2\n3\n4\n')

    def test_playback_to_middle_time(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-e', '1292489690'])
        self.assertEqual(stdout, '')
        self.assert_(re.match(r'Playing until \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \(\d+.\d+\)\.',
            stderr) is not None)
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '0\n1\n2\n')

    def test_playback_from_middle_to_middle_time(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-s', '1292489688', '-e',
            '1292489690'])
        self.assertEqual(stdout, '')
        self.assert_(re.match(r'Playing from \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \(\d+.\d+\) until \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \(\d+.\d+\)\.', stderr) is not None)
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '1\n2\n')

    def test_playback_rate(self):
        logger = start_process(['./rtlog',
            '/localhost/local.host_cxt/Std0.rtc:in.nums',
            '-f', './test/output.rtlog', '-p', '-r', '0.5'])
        time.sleep(5)
        logger.terminate()
        stdout, stderr = logger.communicate()
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(logger.returncode, -15)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('std'), '0\n')

    def test_record(self):
        now = time.time()
        logger = start_process(['./rtlog',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-f', './test/test.rtlog'])
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        time.sleep(1)
        logger.terminate()
        stdout, stderr = logger.communicate()
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(logger.returncode, -15)
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/test.rtlog'])
        self.assert_(self._num_recorded(stdout) > 0)
        self.assert_(self._log_start(stdout) > now)

    def test_record_limit_index(self):
        logger = start_process(['./rtlog',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-f', './test/test.rtlog', '-i', '-e', '5'])
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        stdout, stderr = logger.communicate()
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Recording 5 entries.\n')
        self.assertEqual(logger.returncode, 0)
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/test.rtlog'])
        self.assert_(self._num_recorded(stdout) == 5)

    def test_record_limit_time(self):
        limit = time.time() + 3
        logger = start_process(['./rtlog',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-f', './test/test.rtlog', '-e', '{0}'.format(limit)])
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        stdout, stderr = logger.communicate()
        self.assertEqual(stdout, '')
        m = re.match(r'Recording until \d{4}-\d{2}-\d{2} '
            '\d{2}:\d{2}:\d{2} \((\d+.\d+)\)\.', stderr)
        self.assert_(m is not None)
        self.assert_(abs(float(m.group(1)) - limit) < 0.01)
        self.assertEqual(logger.returncode, 0)
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/test.rtlog'])
        self.assert_(self._num_recorded(stdout) > 0)

    def test_record_timeout(self):
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-f', './test/test.rtlog', '-t', '3'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Recording for 3.0s.')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/test.rtlog'])
        self.assert_(self._num_recorded(stdout) > 0)
        log_length = self._log_end(stdout) - self._log_start(stdout)
        self.assert_(log_length < 3.5)
        self.assert_(log_length > 2.5)

    def test_display_info(self):
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/output.rtlog'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self.assert_('Size: 1.13KiB (1160B)' in stdout)
        self.assert_('Start time: 2010-12-16 17:54:45 (1292489685.35)' in
                stdout)
        self.assert_('First entry time: 2010-12-16 17:54:47 '
                '(1292489687.403273984)' in stdout)
        self.assert_('End time: 2010-12-16 17:54:51 '
                '(1292489691.408852992)' in stdout)
        self.assert_('Number of entries: 5' in stdout)
        self.assert_('Channel 1' in stdout)
        self.assert_('Name: nums' in stdout)
        self.assert_('Data type: TimedLong (RTC.TimedLong)' in stdout)
        self.assert_('/localhost/local.host_cxt/Output0.rtc:out.nums' in
                stdout)

    def test_playback_usermod(self):
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/C20.rtc:input.nums',
            '-f', './test/c1.rtlog', '-p', '--path=./test', '-m', 'MyData'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtlog: End of log reached.')
        self.assertEqual(ret, 0)
        time.sleep(0.5)
        self.assertEqual(self._get_comp_output('c2'),
                'MyData.Bleg(val1=1L, val2=0L)\n'
                'MyData.Bleg(val1=1L, val2=1L)\n'
                'MyData.Bleg(val1=1L, val2=2L)\n'
                'MyData.Bleg(val1=1L, val2=3L)\n'
                'MyData.Bleg(val1=1L, val2=4L)\n')

    def test_record_usermod(self):
        call_process(['./rtact', '/localhost/local.host_cxt/C10.rtc'])
        wait_for_comp('C10.rtc', 'Active')
        stdout, stderr, ret = call_process(['./rtlog',
            '/localhost/local.host_cxt/C10.rtc:output',
            '-f', './test/test.rtlog', '-i', '-e', '5', '--path=./test', '-m',
            'MyData'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Recording 5 entries.')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtlog', '-d', '-f',
            './test/test.rtlog', '--path=./test', '-m', 'MyData'])
        self.assert_(self._num_recorded(stdout) == 5)

    def test_record_text(self):
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        stdout, stderr, ret = call_process(['./rtlog', '-l', 'text',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-f', './test/test.rtlog', '-i', '-e', '5'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Recording 5 entries.')
        self.assertEqual(ret, 0)
        self.assert_(re.match(r"\d+.\d+\s+\('input0', "
            "RTC\.TimedLong\(tm=RTC\.Time\(sec=0L, nsec=0L\), data=\d+\)\)\n",
            load_file('./test/test.rtlog')) is not None)


def rtlog_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtlogTests)


class rtlsTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = launch_comp('output_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')
        wait_for_comp('Output0.rtc')
        self._load_mgr()

    def tearDown(self):
        stop_comp(self._std)
        stop_comp(self._output)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def _load_mgr(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Controller.so'), '-i',
            'ControllerInit', '-c', 'Controller'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Sensor.so'), '-i',
            'SensorInit', '-c', 'Sensor'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Motor.so'), '-i',
            'MotorInit', '-c', 'Motor'])
        self.assertEqual(ret, 0)

    def test_ls_nothing(self):
        stdout, stderr, ret = call_process(['./rtls'])
        self.assertEqual(stdout, 'localhost/')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls', '/'])
        self.assertEqual(stdout, 'localhost/')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_ns(self):
        stdout, stderr, ret = call_process(['./rtls', 'localhost'])
        self.assertEqual(stdout, 'local.host_cxt/')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls', '/localhost'])
        self.assertEqual(stdout, 'local.host_cxt/')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_hc(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt'])
        self.assert_('Std0.rtc' in stdout)
        self.assert_('Output0.rtc' in stdout)
        self.assert_('*Zombie0.rtc' in stdout)
        self.assert_('manager.mgr' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt'])
        self.assert_('Std0.rtc' in stdout)
        self.assert_('Output0.rtc' in stdout)
        self.assert_('*Zombie0.rtc' in stdout)
        self.assert_('manager.mgr' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_mgr_dir(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/manager.mgr'])
        self.assert_('Motor0.rtc' in stdout)
        self.assert_('Controller0.rtc' in stdout)
        self.assert_('Sensor0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/manager.mgr'])
        self.assert_('Motor0.rtc' in stdout)
        self.assert_('Controller0.rtc' in stdout)
        self.assert_('Sensor0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_rtc(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, 'Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_zombie(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '*Zombie0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_mgr_obj(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/manager.mgr'])
        self.assert_('Controller0.rtc' in stdout)
        self.assert_('Motor0.rtc' in stdout)
        self.assert_('Sensor0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_ns_long(self):
        stdout, stderr, ret = call_process(['./rtls', '-l',
            'localhost'])
        self.assertEqual(stdout, '-  -  -  -  -  local.host_cxt')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_hc_long(self):
        stdout, stderr, ret = call_process(['./rtls', '-l',
            'localhost/local.host_cxt'])
        self.assert_('Inactive  1/0  1/0  0/0  0/0  Std0.rtc' in stdout)
        self.assert_('Inactive  2/0  1/0  1/0  0/0  Motor0.rtc' in stdout)
        self.assert_('-         -    -    -    -    manager.mgr' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_rtc_long(self):
        stdout, stderr, ret = call_process(['./rtls', '-l',
            'localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout, 'Inactive  1/0  1/0  0/0  0/0  Std0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_zombie_long(self):
        stdout, stderr, ret = call_process(['./rtls', '-l',
            'localhost/local.host_cxt/Zombie0.rtc'])
        self.assertEqual(stdout, '-  -  -  -  -  *Zombie0.rtc')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_recurse(self):
        stdout, stderr, ret = call_process(['./rtls', '-R'])
        self.assert_('/localhost' in stdout)
        self.assert_('/localhost/local.host_cxt' in stdout)
        self.assert_('Std0.rtc' in stdout)
        self.assert_('Motor0.rtc' in stdout)
        self.assert_('/localhost/local.host_cxt/manager.mgr' in stdout)
        self.assert_('manager.mgr' in stdout)
        self.assert_('*Zombie0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_recurse_long(self):
        stdout, stderr, ret = call_process(['./rtls', '-lR'])
        self.assert_('/localhost' in stdout)
        self.assert_('/localhost/local.host_cxt' in stdout)
        self.assert_('Inactive  1/0  1/0  0/0  0/0  Std0.rtc' in stdout)
        self.assert_('Inactive  2/0  1/0  1/0  0/0  Motor0.rtc' in stdout)
        self.assert_('/localhost/local.host_cxt/manager.mgr' in stdout)
        self.assert_('-         -    -    -    -    manager.mgr' in stdout)
        self.assert_('-         -    -    -    -    *Zombie0.rtc' in stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_ls_port(self):
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtls: Cannot list ports.')
        self.assertEqual(ret, 1)

    def test_ls_noobject(self):
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/NotAComp0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtls: No such object: '
            '/localhost/local.host_cxt/NotAComp0.rtc')
        self.assertEqual(ret, 1)

    def test_ls_notacomp(self):
        stdout, stderr, ret = call_process(['./rtls',
            '/localhost/local.host_cxt/Std0.rtc/'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtls: No such object: '
            '/localhost/local.host_cxt/Std0.rtc/')
        self.assertEqual(ret, 1)


def rtls_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtlsTests)


class rtmgrTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        make_zombie()
        self._mgr = launch_manager()
        wait_for_comp('Std0.rtc')
        self._load_mgr()

    def tearDown(self):
        stop_comp(self._std)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def _load_mgr(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Controller.so'), '-i',
            'ControllerInit'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Sensor.so'), '-i',
            'SensorInit', '-c', 'Sensor'])
        self.assertEqual(ret, 0)

    def _grab_section(self, stdout, sec, next_sec=''):
        self.assert_(sec in stdout)
        if not next_sec:
            next_sec = '$'
        return re.match(r'.*?\n{0}\n(.*?){1}'.format(sec, next_sec), stdout,
            re.S).groups()[0]

    def test_load_mod(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Motor.so'), '-i', 'MotorInit'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/manager.mgr'])
        loaded = self._grab_section(stdout, 'Loaded modules:')
        self.assert_(os.path.join(COMP_LIB_PATH, 'Motor.so') in loaded)

    def test_load_mod_no_init(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-l',
            os.path.join(COMP_LIB_PATH, 'Motor.so')])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: No initialisation function '
            'specified.')
        self.assertEqual(ret, 1)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/manager.mgr'])
        loaded = self._grab_section(stdout, 'Loaded modules:')
        self.assert_(os.path.join(COMP_LIB_PATH, 'Motor.so') not in loaded)

    def test_create_rtc(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/manager.mgr'])
        self.assert_('Controller0.rtc' in stdout)
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/'])
        self.assert_('Controller0.rtc' in stdout)

    def test_delete_rtc(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-d', 'Sensor0'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/manager.mgr'])
        self.assert_('Sensor0.rtc' not in stdout)
        stdout, stderr, ret = call_process(['./rtls',
            'localhost/local.host_cxt/'])
        self.assert_('Sensor0.rtc' not in stdout)

    def test_unload_mod(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr', '-u',
            os.path.join(COMP_LIB_PATH, 'Controller.so')])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/manager.mgr'])
        loaded = self._grab_section(stdout, 'Loaded modules:')
        self.assert_(os.path.join(COMP_LIB_PATH, 'Controller.so') not in loaded)

    def test_port(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/manager.mgr:port', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: Not a manager: '
            '/localhost/local.host_cxt/manager.mgr:port')
        self.assertEqual(ret, 1)

    def test_rtc(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/Std0.rtc', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: Not a manager: '
            '/localhost/local.host_cxt/Std0.rtc')
        self.assertEqual(ret, 1)

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: Not a manager: '
            '/localhost/local.host_cxt')
        self.assertEqual(ret, 1)

    def test_ns(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: Not a manager: '
            '/localhost')
        self.assertEqual(ret, 1)

    def test_zombie(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/Zombie0.rtc', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: Zombie object: '
            '/localhost/local.host_cxt/Zombie0.rtc')
        self.assertEqual(ret, 1)

    def test_noobject(self):
        stdout, stderr, ret = call_process(['./rtmgr',
            '/localhost/local.host_cxt/NotAComp.rtc', '-c', 'Controller'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtmgr: No such object: '
            '/localhost/local.host_cxt/NotAComp.rtc')
        self.assertEqual(ret, 1)


def rtmgr_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtmgrTests)


class rtstodotTests(unittest.TestCase):
    def test_stdin(self):
        sys = load_file('./test/sys.rtsys')
        p = subprocess.Popen('./rtstodot', stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(sys)
        self.assertEqual(stderr, '')
        self.assertEqual(p.returncode, 0)
        sample = load_file('./test/sys.dot')
        self.assertEqual(sample, stdout)

    def test_file(self):
        stdout, stderr, ret = call_process(['./rtstodot', './test/sys.rtsys'])
        sample = load_file('./test/sys.dot')
        self.assertEqual(sample.rstrip(), stdout)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)


def rtstodot_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtstodotests)


class rtprintTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._output = launch_comp('output_comp')
        self._c1 = launch_comp('c1_comp')
        wait_for_comp('Output0.rtc')
        wait_for_comp('C10.rtc')
        call_process(['./rtact', '/localhost/local.host_cxt/Output0.rtc'])
        call_process(['./rtact', '/localhost/local.host_cxt/C10.rtc'])
        wait_for_comp('Output0.rtc', 'Active')
        wait_for_comp('C10.rtc', 'Active')

    def tearDown(self):
        stop_comp(self._output)
        stop_comp(self._c1)
        stop_ns(self._ns)

    def test_print(self):
        p = start_process(['./rtprint',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        time.sleep(1)
        p.terminate()
        stdout, stderr = p.communicate()
        self.assert_(re.match(r'\[0\.0+\]\s\d+\n', stdout) is not None)
        self.assertEqual(stderr, '')
        self.assertEqual(p.returncode, -15)

    def test_print_count_limit(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/Output0.rtc:out', '-n', '2'])
        self.assert_(re.match(r'\[0\.0+\]\s\d+\n\[0\.0+\]\s\d+$', stdout) is not None)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_print_time_limit(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/Output0.rtc:out', '-t', '1'])
        self.assert_(re.match(r'\[0\.0+\]\s\d+\n', stdout) is not None)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_user_mod(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/C10.rtc:output', '-n', '1',
            '-p', './test', '-m', 'MyData'])
        self.assert_(re.match(r'MyData\.Bleg\(val1=1L, val2=\d+L\)', stdout) is not None)
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)

    def test_mod_no_path(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/C10.rtc:output', '-n', '1',
            '-m', 'MyData'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtprint: No module named MyData')
        self.assertEqual(ret, 1)

    def test_bad_comp(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/NotAComp0.rtc:out', '-n', '2'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtprint: No such object: '
            '/localhost/local.host_cxt/NotAComp0.rtc')
        self.assertEqual(ret, 1)

    def test_bad_port(self):
        stdout, stderr, ret = call_process(['./rtprint',
            '/localhost/local.host_cxt/Output0.rtc:noport', '-n', '2'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtprint: Port not found: '
            '/localhost/local.host_cxt/Output0.rtc:noport')
        self.assertEqual(ret, 1)


def rtprint_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtprintTests)


class rtresetTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._err = launch_comp('err_comp')
        make_zombie()
        self._mgr = launch_manager()
        call_process(['./rtact', '/localhost/local.host_cxt/Err0.rtc'])
        wait_for_comp('Err0.rtc', state='Error')

    def tearDown(self):
        stop_comp(self._err)
        clean_zombies()
        stop_manager(self._mgr)
        stop_ns(self._ns)

    def test_success(self):
        stdout, stderr, ret = call_process(['./rtreset',
            '/localhost/local.host_cxt/Err0.rtc'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Err0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')

    def test_context(self):
        stdout, stderr, ret = call_process(['./rtreset',
            '/localhost/local.host_cxt'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr,
            'rtreset: Not a component: /localhost/local.host_cxt')
        self.assertEqual(ret, 1)


    def test_manager(self):
        test_notacomp(self, './rtreset', obj1='manager.mgr')

    def test_port(self):
        test_notacomp(self, './rtreset', obj1='Err0.rtc:in')

    def test_trailing_slash(self):
        test_notacomp(self, './rtreset', obj1='Err0.rtc/')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Err0.rtc'])
        self.assertEqual(stdout.split()[1], 'Error')

    def test_no_object(self):
        test_noobject(self, './rtreset', obj1='NotAComp0.rtc')

    def test_zombie_object(self):
        test_zombie(self, './rtreset', obj1='Zombie0.rtc')

    def test_no_arg(self):
        stdout, stderr, ret = call_process('./rtreset')
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtreset: No component specified.')
        self.assertEqual(ret, 1)


def rtreset_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtresetTests)


class rtresurrectTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = None
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        if self._output:
            stop_comp(self._output)
        stop_ns(self._ns)

    def test_noprobs(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '2')
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assert_('/localhost/local.host_cxt/Std0.rtc:in' in stdout)
        stdout, stderr, ret = call_process(['./rtconf', '-s', 'set2',
            '/localhost/local.host_cxt/Std0.rtc', 'get', 'param'])
        self.assertEqual(stdout, '42')

    def test_missing_comp(self):
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtresurrect: Required action failed: '
            'Required component missing: '
            '/localhost/local.host_cxt/Output0.rtc')
        self.assertEqual(ret, 1)

    def test_missing_port(self):
        self._output = launch_comp('output_noport_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtresurrect: Required action failed: '
                'Required port not found: out')
        self.assertEqual(ret, 1)

    def test_dry_run(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys', '--dry-run'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self.assert_('Check for required component "RTC:Geoffrey '
            'Biggs:test:Std:1.0", "Std0" at path '
            '/localhost/local.host_cxt/Std0.rtc (Required)' in stdout)
        self.assert_('Check for required component "RTC:Geoffrey '
            'Biggs:Test:Output:1.0", "Output0" at path '
            '/localhost/local.host_cxt/Output0.rtc (Required)' in stdout)
        self.assert_('Check for required port "in" on component at path '
            '/localhost/local.host_cxt/Std0.rtc (Required)' in stdout)
        self.assert_('Check for required port "out" on component at path '
            '/localhost/local.host_cxt/Output0.rtc (Required)' in stdout)
        self.assert_('Connect /localhost/local.host_cxt/Output0.rtc:out to '
            '/localhost/local.host_cxt/Std0.rtc:in with ID '
            'connection_id0 and properties' in stdout)
        self.assert_('Set parameter "param" in set "set2" on component at '
            'path /localhost/local.host_cxt/Std0.rtc to "42"' in stdout)
        self.assert_('Set configuration set "default" active on component at '
            'path /localhost/local.host_cxt/Std0.rtc' in stdout)

    def test_existing_con_diff_id(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            'localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout.count('+Connected to  '
            '/localhost/local.host_cxt/Output0.rtc:out'), 2)

    def test_existing_con_same_id(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out',
            '-i', 'connection_id0'])
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtresurrect',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            'localhost/local.host_cxt/Std0.rtc:in'])
        self.assertEqual(stdout.count('+Connected to  '
            '/localhost/local.host_cxt/Output0.rtc:out'), 1)


def rtresurrect_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtresurrectTests)


class rtstartTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = None
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        if self._output:
            stop_comp(self._output)
        stop_ns(self._ns)

    def test_noprobs(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtstart', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(ret, 0)
        self.assert_('Activate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0 (Required)' in stderr)
        self.assert_('Activate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0 (Required)' in stderr)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')

    def test_missing_comp(self):
        stdout, stderr, ret = call_process(['./rtstart', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'rtstart: Required action failed: '
            'Required component missing: '
            '/localhost/local.host_cxt/Output0.rtc')
        self.assertEqual(ret, 1)

    def test_already_active(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt/Std0.rtc'])
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtstart', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(ret, 0)
        self.assert_('Activate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0 (Required)' in stderr)
        self.assert_('Activate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0 (Required)' in stderr)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')

    def test_dry_run(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtstart',
            './test/sys.rtsys', '--dry-run'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self.assert_('Check for required component "RTC:Geoffrey '
            'Biggs:test:Std:1.0", "Std0" at path '
            '/localhost/local.host_cxt/Std0.rtc (Required)' in stdout)
        self.assert_('Check for required component "RTC:Geoffrey '
            'Biggs:Test:Output:1.0", "Output0" at path '
            '/localhost/local.host_cxt/Output0.rtc (Required)' in stdout)
        self.assert_('Activate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0 (Required)' in stdout)
        self.assert_('Activate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0 (Required)' in stdout)


def rtstart_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtstartTests)


class rtstopTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = None
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        if self._output:
            stop_comp(self._output)
        stop_ns(self._ns)

    def test_noprobs(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt/Std0.rtc'])
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt/Output0.rtc'])
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtstop', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(ret, 0)
        self.assert_('Deactivate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0' in stderr)
        self.assert_('Deactivate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0' in stderr)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')

    def test_missing_comp(self):
        stdout, stderr, ret = call_process(['./rtstop', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assert_('Action failed: Component missing: '
            '/localhost/local.host_cxt/Output0.rtc' in stderr)
        self.assertEqual(ret, 0)

    def test_already_inactive(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtact',
            '/localhost/local.host_cxt/Std0.rtc'])
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Active')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtstop', './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(ret, 0)
        self.assert_('Deactivate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0' in stderr)
        self.assert_('Deactivate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0' in stderr)
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Std0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')
        stdout, stderr, ret = call_process(['./rtcat',
            '/localhost/local.host_cxt/Output0.rtc'])
        self.assertEqual(stdout.split()[1], 'Inactive')

    def test_dry_run(self):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtstop',
            './test/sys.rtsys', '--dry-run'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self.assert_('Deactivate /localhost/local.host_cxt/Std0.rtc in '
            'execution context 0' in stdout)
        self.assert_('Deactivate /localhost/local.host_cxt/Output0.rtc in '
            'execution context 0' in stdout)


def rtstop_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtstopTests)


class rtteardownTests(unittest.TestCase):
    def setUp(self):
        self._ns = start_ns()
        self._std = launch_comp('std_comp')
        self._output = None
        wait_for_comp('Std0.rtc')

    def tearDown(self):
        stop_comp(self._std)
        if self._output:
            stop_comp(self._output)
        stop_ns(self._ns)

    def _setup_comp(self, id=''):
        self._output = launch_comp('output_comp')
        wait_for_comp('Output0.rtc')
        args = ['./rtcon',
            '/localhost/local.host_cxt/Std0.rtc:in',
            '/localhost/local.host_cxt/Output0.rtc:out']
        if id:
            args += ['-i', id]
        stdout, stderr, ret = call_process(args)

    def test_noprobs(self):
        self._setup_comp('connection_id0')
        stdout, stderr, ret = call_process(['./rtteardown',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        stdout, stderr, ret = call_process(['./rtcat', '-l',
            '/localhost/local.host_cxt/Std0.rtc:in'])
        self.assert_('Connected to' not in stdout)

    def test_missing_comp(self):
        stdout, stderr, ret = call_process(['./rtteardown',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Action failed: Source component missing: '
            '/localhost/local.host_cxt/Output0.rtc')
        self.assertEqual(ret, 0)

    def test_missing_port(self):
        self._output = launch_comp('output_noport_comp')
        wait_for_comp('Output0.rtc')
        stdout, stderr, ret = call_process(['./rtteardown',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Action failed: Source port missing: '
            '/localhost/local.host_cxt/Output0.rtc:out')
        self.assertEqual(ret, 0)

    def test_wrong_id(self):
        self._setup_comp('other_id')
        stdout, stderr, ret = call_process(['./rtteardown',
            './test/sys.rtsys'])
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Action failed: No connection from '
            '/localhost/local.host_cxt/Output0.rtc:out with ID connection_id0')
        self.assertEqual(ret, 0)

    def test_dry_run(self):
        self._setup_comp('connection_id0')
        stdout, stderr, ret = call_process(['./rtteardown',
            './test/sys.rtsys', '--dry-run'])
        self.assertEqual(stderr, '')
        self.assertEqual(ret, 0)
        self.assertEqual(stdout, 'Disconnect '
            '/localhost/local.host_cxt/Output0.rtc:out from '
            '/localhost/local.host_cxt/Std0.rtc:in with ID connection_id0')


def rtteardown_suite():
    return unittest.TestLoader().loadTestsFromTestCase(rtteardownTests)


def suite():
    return unittest.TestSuite([rtact_suite(), rtdeact_suite(),
        rtreset_suite(), rtcat_suite(), rtcheck_suite(), rtcomp_suite(),
        rtcon_suite(), rtconf_suite(), rtcryo_suite(), rtcwd_suite(),
        rtdel_suite(), rtdis_suite(), rtexit_suite(), rtfind_suite(),
        rtinject_suite(), rtlog_suite(), rtls_suite(), rtmgr_suite(),
        rtprint_suite(), rtresurrect_suite(), rtstart_suite(),
        rtstodot_suite(), rtstop_suite(), rtteardown_suite()])


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        COMP_LIB_PATH = sys.argv[1]
        sys.argv = [sys.argv[0]] + sys.argv[2:]
    unittest.main()

