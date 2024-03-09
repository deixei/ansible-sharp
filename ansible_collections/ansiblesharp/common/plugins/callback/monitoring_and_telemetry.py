#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

## Research
# https://github.com/ansible-collections/community.general/blob/main/plugins/callback/opentelemetry.py
# https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/monitor/azure-monitor-opentelemetry-exporter
# https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html

DOCUMENTATION = '''
    author: Marcio Parente
    name: monitoring_and_telemetry
    type: notification
    short_description: Create distributed traces with Open Telemetry
    version_added: 3.7.0
    description:
      - This callback creates distributed traces for each Ansible task with Open Telemetry.
      - You can configure the Open Telemetry exporter and SDK with environment variables.
      - See as reference U(https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html).
      - See as reference U(https://opentelemetry-python.readthedocs.io/en/latest/sdk/environment_variables.html#opentelemetry-sdk-environment-variables).
    options:
      MON_ECOSYSTEM:
        default: "ecosystem-unknown"
        type: str
        description:
          - The ecosystem code name.
        var:
          - name: MON_ECOSYSTEM
        env:
          - name: MON_ECOSYSTEM
        ini:
          - section: callback_monitoring_and_telemetry
            key: MON_ECOSYSTEM
      MON_PROJECT:
        default: "project-unknown"
        type: str
        description:
          - The project code name.
        var:
          - name: MON_PROJECT
        env:
          - name: MON_PROJECT
        ini:
          - section: callback_monitoring_and_telemetry
            key: MON_PROJECT            
      MON_WORKLOAD:
        default: "workload-unknown"
        type: str
        description:
          - The asc workload code name.
        var:
          - name: MON_WORKLOAD
        env:
          - name: MON_WORKLOAD
        ini:
          - section: callback_monitoring_and_telemetry
            key: MON_WORKLOAD              
      hide_task_arguments:
        default: false
        type: bool
        description:
          - Hide the arguments for a task.
        env:
          - name: ANSIBLE_OPENTELEMETRY_HIDE_TASK_ARGUMENTS
        ini:
          - section: callback_monitoring_and_telemetry
            key: hide_task_arguments
            version_added: 5.3.0
      enable_from_environment:
        type: str
        description:
          - Whether to enable this callback only if the given environment variable exists and it is set to V(true).
          - This is handy when you use Configuration as Code and want to send distributed traces
            if running in the CI rather when running Ansible locally.
          - For such, it evaluates the given O(enable_from_environment) value as environment variable
            and if set to true this plugin will be enabled.
        env:
          - name: ANSIBLE_OPENTELEMETRY_ENABLE_FROM_ENVIRONMENT
        ini:
          - section: callback_monitoring_and_telemetry
            key: enable_from_environment
            version_added: 5.3.0
        version_added: 3.8.0
      traceparent:
        default: None
        type: str
        description:
          - The L(W3C Trace Context header traceparent,https://www.w3.org/TR/trace-context-1/#traceparent-header).
        env:
          - name: TRACEPARENT
      disable_logs:
        default: false
        type: bool
        description:
          - Disable sending logs.
        env:
          - name: ANSIBLE_OPENTELEMETRY_DISABLE_LOGS
        ini:
          - section: callback_monitoring_and_telemetry
            key: disable_logs
        version_added: 5.8.0
      disable_attributes_in_logs:
        default: false
        type: bool
        description:
          - Disable populating span attributes to the logs.
        env:
          - name: ANSIBLE_OPENTELEMETRY_DISABLE_ATTRIBUTES_IN_LOGS
        ini:
          - section: callback_monitoring_and_telemetry
            key: disable_attributes_in_logs
        version_added: 7.1.0
    requirements:
      - azure-monitor-opentelemetry

'''


EXAMPLES = '''
examples: |
  Enable the plugin in ansible.cfg:
    [defaults]
    callbacks_enabled = asc.common.monitoring_and_telemetry
    [callback_monitoring_and_telemetry]
    MON_ECOSYSTEM = ecosystem-name-cloud-platform
    MON_PROJECT = project-examples1

  Set the environment variable:
    export OTEL_EXPORTER_OTLP_ENDPOINT=<your endpoint (OTLP/HTTP)>
    export OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer your_otel_token"
    export ANSIBLE_OPENTELEMETRY_ENABLED=true
'''

import getpass
import os
import socket
import sys

from ansible_collections.ansiblesharp.common.plugins.module_utils.common import MonitoringAttributes


import time
import uuid

from collections import OrderedDict
from os.path import basename

from ansible.errors import AnsibleError
from ansible.module_utils.six import raise_from
from ansible.plugins.callback import CallbackBase
from urllib.parse import urlparse

try:
    from opentelemetry import trace

    from azure.monitor.opentelemetry import configure_azure_monitor   
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    
    from opentelemetry.propagate import extract
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.trace import SpanKind
    from opentelemetry.sdk.trace.export import SpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_INSTANCE_ID
    from opentelemetry.trace.status import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (BatchSpanProcessor)

except ImportError as imp_exc:
    OTEL_LIBRARY_IMPORT_ERROR = imp_exc
else:
    OTEL_LIBRARY_IMPORT_ERROR = None


time_ns = time.time_ns

# Set to true to print the trace to stdout
asc_TRACE = None

class TaskData:
    """
    Data about an individual task.
    """

    def __init__(self, uuid, name, path, play, action, args):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.play = play
        self.host_data = OrderedDict()
        self.start = time_ns()
        self.finish = time_ns()
        self.action = action
        self.args = args
        self.dump = None

    def add_host(self, host):
        if host.uuid in self.host_data:
            if host.status == 'included':
                # concatenate task include output from multiple items
                host.result = '%s\n%s' % (self.host_data[host.uuid].result, host.result)
            else:
                return

        self.host_data[host.uuid] = host


class HostData:
    """
    Data about an individual host.
    """

    def __init__(self, uuid, name, status, result):
        self.uuid = uuid
        self.name = name
        self.status = status
        self.result = result
        self.finish = time_ns()

class PlaybookData:
    """
    Data about an individual playbook.
    """

    def __init__(self, ansible_playbook, ecosystem, project, workload):
        #self._display.warning("The `ansible_playbook` has been set as {0}.".format(vars(playbook._loader)))
        self.file_dir = ansible_playbook._basedir
        self.file_name = ansible_playbook._file_name
        self.name = basename(ansible_playbook._file_name)


        self.ecosystem = ecosystem
        self.project = project
        self.workload = workload

        self.start = time_ns()
        self.finish = time_ns()

        self.plays = OrderedDict()
    
    

class PlayData:
    """
    Data about an individual play.
    """

    def __init__(self, play, ecosystem, project, workload):
        self.ansible_play = play

        play_name = self.ansible_play.get_name().strip()
        play_vars = self.ansible_play.get_vars()
        
        self.uuid = play._uuid
        self.name = play_name

        self.start = time_ns()
        self.finish = time_ns()

        self.tasks = OrderedDict()

        self.ecosystem = play_vars.get("MON_ECOSYSTEM", ecosystem)
        self.project = play_vars.get("MON_PROJECT", project)
        self.workload = play_vars.get("MON_WORKLOAD", workload)

        self.ecosystem = ecosystem
        self.project = project
        self.workload = workload

        

    def add_task(self, task: TaskData):
        if task._uuid in self.tasks:
            return self.tasks[task.uuid]

        self.tasks[task.uuid] = task

        return self.tasks[task.uuid]


class OpenTelemetrySource(object):
    def __init__(self, display):
        self.ansible_playbook = None
        self.ansible_version = None
        self.session = str(uuid.uuid4())

        self.host = socket.gethostname()
        try:
            self.ip_address = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            self.ip_address = None
        self.user = getpass.getuser()

        self._display = display


    def traceparent_context(self, traceparent):
        carrier = dict()
        carrier['traceparent'] = traceparent
        return TraceContextTextMapPropagator().extract(carrier=carrier)

    def start_play(self, plays_data, play, ecosystem, project, workload):
        """ record the start of a play """
        uuid = play._uuid

        if uuid in plays_data:
            return plays_data[uuid]

        plays_data[uuid] = PlayData(play, ecosystem, project, workload)

        return plays_data[uuid]
    
    def finish_play(self, plays_data, play_data: PlayData):
        """ record the results of a play """

        play_uuid = play_data.uuid
        play = plays_data[play_uuid]
        play.finish = time_ns()

        return plays_data[play_uuid]

    def start_task(self, play_data: PlayData, hide_task_arguments, task):
        """ record the start of a task for one or more hosts """

        uuid = task._uuid

        if uuid in play_data.tasks:
            return play_data.tasks[uuid]

        name = task.get_name().strip()
        path = task.get_path()
        action = task.action
        args = None

        if not task.no_log and not hide_task_arguments:
            args = task.args

        play_data.tasks[uuid] = TaskData(uuid, name, path, play_data.name, action, args)

        return play_data.tasks[uuid]

    def finish_task(self, play_data: PlayData, status, result, dump):
        """ record the results of a task for a single host """

        task_uuid = result._task._uuid

        if hasattr(result, '_host') and result._host is not None:
            host_uuid = result._host._uuid
            host_name = result._host.name
        else:
            host_uuid = 'include'
            host_name = 'include'
        
        play_data.tasks[task_uuid].finish = time_ns()
        
        task = play_data.tasks[task_uuid]

        if self.ansible_version is None and hasattr(result, '_task_fields') and result._task_fields['args'].get('_ansible_version'):
            self.ansible_version = result._task_fields['args'].get('_ansible_version')

        task.dump = dump
        task.add_host(HostData(host_uuid, host_name, status, result))

    def generate_distributed_traces(self, ansible_playbook:PlaybookData, plays_data: OrderedDict, status, traceparent, disable_logs, disable_attributes_in_logs):
        """ generate distributed traces from the collected TaskData and HostData """

        tasks = []
        for p_uuid, p in plays_data.items():

            parent_start_time = None
            for task_uuid, task in p.tasks.items():
                if parent_start_time is None:
                    parent_start_time = task.start
                tasks.append(task)

        # from opentelemetry.semconv.resource import ResourceAttributes
        # https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-configuration?tabs=python#set-the-cloud-role-name-and-the-cloud-role-instance
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({
                    
                    ResourceAttributes.HOST_NAME: ansible_playbook.ecosystem,
                    ResourceAttributes.HOST_ID: ansible_playbook.ecosystem,
                    ResourceAttributes.SERVICE_NAME: ansible_playbook.workload,
                    ResourceAttributes.SERVICE_NAMESPACE: ansible_playbook.project,
                    ResourceAttributes.OS_VERSION: "1.0.0",
                    ResourceAttributes.OS_TYPE: "ansible",
                    ResourceAttributes.OS_DESCRIPTION: "ansible playbooks",
                    ResourceAttributes.OS_NAME: "asc ansible",
                    ResourceAttributes.USER_AGENT_ORIGINAL: "Edge 1.0.0 asc",
                    
                    })
            )
        )
        

        exporter = AzureMonitorTraceExporter.from_connection_string(MonitoringAttributes.INSTRUMENTATION_KEY_CONNECTION_STRING)
        processor = BatchSpanProcessor(exporter)
        
        #processor = BatchSpanProcessor(SpanExporter())
        
        trace.get_tracer_provider().add_span_processor(processor)

        tracer = trace.get_tracer(__name__)

        ansible_playbook_name = format("{0}/{1}/{2}/{3}").format(ansible_playbook.ecosystem, ansible_playbook.project, ansible_playbook.workload, ansible_playbook.name)

        with tracer.start_as_current_span(ansible_playbook_name, context=self.traceparent_context(traceparent),
                                          start_time=parent_start_time, kind=SpanKind.CLIENT) as parent:
            parent.set_status(status)
            
            parent.set_attribute("asc.ecosystem", ansible_playbook.ecosystem)
            parent.set_attribute("asc.project", ansible_playbook.project)
            parent.set_attribute("asc.workload", ansible_playbook.workload)

            # Populate trace metadata attributes
            if self.ansible_version is not None:
                parent.set_attribute("ansible.version", self.ansible_version)
            parent.set_attribute("ansible.session", self.session)
            parent.set_attribute("ansible.host.name", self.host)
            if self.ip_address is not None:
                parent.set_attribute("ansible.host.ip", self.ip_address)
            parent.set_attribute("ansible.host.user", self.user)

            for p_uuid, p in plays_data.items():
                with tracer.start_as_current_span(p.name, context=self.traceparent_context(traceparent),
                                                  start_time=p.start, kind=SpanKind.SERVER, end_on_exit=False) as playspan:
                    playspan.end(end_time=p.finish)

                    for task_uuid, task in p.tasks.items():
                        # Assuming task.start and task.finish are time in nanoseconds
                        #duration_ns = task.finish - task.start
                        # Convert duration to milliseconds
                        #duration_in_ms = duration_ns / 1_000_000
                        #duration_in_ms = int(duration_ns / 1_000_000)
                        #tc.track_pageview(name=task.action, url=task.path, duration=duration_in_ms)

                        
                        for h_uuid, h in task.host_data.items():
                            with tracer.start_as_current_span(task.action, start_time=task.start, end_on_exit=False) as span:
                                self.update_span_data(task, h, span, disable_logs, disable_attributes_in_logs)
                    
                    
        # Send all pending telemetry
        #tc.flush()

            #for task in tasks:
            #    for host_uuid, host_data in task.host_data.items():
            #        with tracer.start_as_current_span(task.name, start_time=task.start, end_on_exit=False) as span:
            #            self.update_span_data(task, host_data, span, disable_logs, disable_attributes_in_logs)

    def update_span_data(self, task_data, host_data, span, disable_logs, disable_attributes_in_logs):
        """ update the span with the given TaskData and HostData """

        name = '[%s] %s: %s' % (host_data.name, task_data.play, task_data.name)

        message = 'success'
        res = {}
        rc = 0
        status = Status(status_code=StatusCode.OK)
        if host_data.status != 'included':
            # Support loops
            if 'results' in host_data.result._result:
                if host_data.status == 'failed':
                    message = self.get_error_message_from_results(host_data.result._result['results'], task_data.action)
                    enriched_error_message = self.enrich_error_message_from_results(host_data.result._result['results'], task_data.action)
            else:
                res = host_data.result._result
                rc = res.get('rc', 0)
                if host_data.status == 'failed':
                    message = self.get_error_message(res)
                    enriched_error_message = self.enrich_error_message(res)

            if host_data.status == 'failed':
                status = Status(status_code=StatusCode.ERROR, description=message)
                # Record an exception with the task message
                span.record_exception(BaseException(enriched_error_message))
            elif host_data.status == 'skipped':
                message = res['skip_reason'] if 'skip_reason' in res else 'skipped'
                status = Status(status_code=StatusCode.UNSET)
            elif host_data.status == 'ignored':
                status = Status(status_code=StatusCode.UNSET)

        span.set_status(status)

        # Create the span and log attributes
        attributes = {
            "ansible.task.module": task_data.action,
            "ansible.task.message": message,
            "ansible.task.name": name,
            "ansible.task.result": rc,
            "ansible.task.host.name": host_data.name,
            "ansible.task.host.status": host_data.status
        }
        if isinstance(task_data.args, dict) and "gather_facts" not in task_data.action:
            names = tuple(self.transform_ansible_unicode_to_str(k) for k in task_data.args.keys())
            values = tuple(self.transform_ansible_unicode_to_str(k) for k in task_data.args.values())
            attributes[("ansible.task.args.name")] = names
            attributes[("ansible.task.args.value")] = values

        self.set_span_attributes(span, attributes)

        # This will allow to enrich the service map
        self.add_attributes_for_service_map_if_possible(span, task_data)
        # Send logs
        if not disable_logs:
            # This will avoid populating span attributes to the logs
            span.add_event(task_data.dump, attributes={} if disable_attributes_in_logs else attributes)
            span.end(end_time=host_data.finish)

    def set_span_attributes(self, span, attributes):
        """ update the span attributes with the given attributes if not None """

        if span is None and self._display is not None:
            self._display.warning('span object is None. Please double check if that is expected.')
        else:
            if attributes is not None:
                span.set_attributes(attributes)

    def add_attributes_for_service_map_if_possible(self, span, task_data):
        """Update the span attributes with the service that the task interacted with, if possible."""

        redacted_url = self.parse_and_redact_url_if_possible(task_data.args)
        if redacted_url:
            span.set_attribute("http.url", redacted_url.geturl())

    @staticmethod
    def parse_and_redact_url_if_possible(args):
        """Parse and redact the url, if possible."""

        try:
            parsed_url = urlparse(OpenTelemetrySource.url_from_args(args))
        except ValueError:
            return None

        if OpenTelemetrySource.is_valid_url(parsed_url):
            return OpenTelemetrySource.redact_user_password(parsed_url)
        return None

    @staticmethod
    def url_from_args(args):
        # the order matters
        url_args = ("url", "api_url", "baseurl", "repo", "server_url", "chart_repo_url", "registry_url", "endpoint", "uri", "updates_url")
        for arg in url_args:
            if args is not None and args.get(arg):
                return args.get(arg)
        return ""

    @staticmethod
    def redact_user_password(url):
        return url._replace(netloc=url.hostname) if url.password else url

    @staticmethod
    def is_valid_url(url):
        if all([url.scheme, url.netloc, url.hostname]):
            return "{{" not in url.hostname
        return False

    @staticmethod
    def transform_ansible_unicode_to_str(value):
        parsed_url = urlparse(str(value))
        if OpenTelemetrySource.is_valid_url(parsed_url):
            return OpenTelemetrySource.redact_user_password(parsed_url).geturl()
        return str(value)

    @staticmethod
    def get_error_message(result):
        if result.get('exception') is not None:
            return OpenTelemetrySource._last_line(result['exception'])
        return result.get('msg', 'failed')

    @staticmethod
    def get_error_message_from_results(results, action):
        for result in results:
            if result.get('failed', False):
                return ('{0}({1}) - {2}').format(action, result.get('item', 'none'), OpenTelemetrySource.get_error_message(result))

    @staticmethod
    def _last_line(text):
        lines = text.strip().split('\n')
        return lines[-1]

    @staticmethod
    def enrich_error_message(result):
        message = result.get('msg', 'failed')
        exception = result.get('exception')
        stderr = result.get('stderr')
        return ('message: "{0}"\nexception: "{1}"\nstderr: "{2}"').format(message, exception, stderr)

    @staticmethod
    def enrich_error_message_from_results(results, action):
        message = ""
        for result in results:
            if result.get('failed', False):
                message = ('{0}({1}) - {2}\n{3}').format(action, result.get('item', 'none'), OpenTelemetrySource.enrich_error_message(result), message)
        return message


class CallbackModule(CallbackBase):
    """
    This callback creates distributed traces.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'ansiblesharp.common.monitoring_and_telemetry'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.hide_task_arguments = None
        self.disable_attributes_in_logs = None
        self.disable_logs = None
        self.ansible_playbook = None
        self.play_name = None
        self.plays_data = None
        self.errors = 0
        self.disabled = False
        self.traceparent = True
        
        self.current_play = None
        
        self.MON_ECOSYSTEM = None
        self.MON_PROJECT = None
        self.MON_WORKLOAD = None

        if OTEL_LIBRARY_IMPORT_ERROR:
            raise_from(
                AnsibleError('[Ansible-Sharp ERROR]: The `azure-monitor-opentelemetry` must be installed to use this plugin'),
                OTEL_LIBRARY_IMPORT_ERROR)

        self.plays_data = OrderedDict()

        self.asctelemetry = OpenTelemetrySource(display=self._display)

        RequestsInstrumentor().instrument()


    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys,
                                                var_options=var_options,
                                                direct=direct)
        
        environment_variable = self.get_option('enable_from_environment')
        if environment_variable is not None and os.environ.get(environment_variable, 'false').lower() != 'true':
            self.disabled = True
            self._display.warning("The `enable_from_environment` option has been set and {0} is not enabled. "
                                  "Disabling the `opentelemetry` callback plugin.".format(environment_variable))

        self.hide_task_arguments = self.get_option('hide_task_arguments')

        self.disable_attributes_in_logs = self.get_option('disable_attributes_in_logs')

        self.disable_logs = self.get_option('disable_logs')

        # See https://github.com/open-telemetry/opentelemetry-specification/issues/740
        self.traceparent = self.get_option('traceparent')

        self.MON_ECOSYSTEM = self.get_option('MON_ECOSYSTEM')
        self.MON_PROJECT = self.get_option('MON_PROJECT')
        self.MON_WORKLOAD = self.get_option('MON_WORKLOAD')

        if asc_TRACE:
            self._display.warning("The `MON_ECOSYSTEM` has been set as {0}.".format(self.MON_ECOSYSTEM))
            self._display.warning("The `MON_PROJECT` has been set as {0}.".format(self.MON_PROJECT))
            self._display.warning("The `MON_WORKLOAD` has been set as {0}.".format(self.MON_WORKLOAD))

    def v2_playbook_on_start(self, playbook):
        self.ansible_playbook = PlaybookData(playbook, self.MON_ECOSYSTEM, self.MON_PROJECT, self.MON_WORKLOAD)

    def v2_playbook_on_play_start(self, play):
        self.play_name = play.get_name()

        if self.current_play is None or (self.current_play.uuid is not play._uuid):
            self.current_play = self.asctelemetry.start_play(self.plays_data, play, 
                                                              self.MON_ECOSYSTEM, 
                                                              self.MON_PROJECT, 
                                                              self.MON_WORKLOAD)
        else:
            self.asctelemetry.finish_play(self.plays_data, self.current_play)
            self.current_play = None


    def v2_runner_on_no_hosts(self, task):
        self.asctelemetry.start_task(
            self.current_play,
            self.hide_task_arguments,
            self.play_name,
            task
        )
        

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.asctelemetry.start_task(
            self.current_play,
            self.hide_task_arguments,
            task
        )

    def v2_playbook_on_cleanup_task_start(self, task):
        self.asctelemetry.start_task(
            self.current_play,
            self.hide_task_arguments,
            task
        )

    def v2_playbook_on_handler_task_start(self, task):
        self.asctelemetry.start_task(
            self.current_play,
            self.hide_task_arguments,
            task
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            status = 'ignored'
        else:
            status = 'failed'
            self.errors += 1

        self.asctelemetry.finish_task(
            self.current_play,
            status,
            result,
            self._dump_results(result._result)
        )

    def v2_runner_on_ok(self, result):
        self.asctelemetry.finish_task(
            self.current_play,
            'ok',
            result,
            self._dump_results(result._result)
        )

    def v2_runner_on_skipped(self, result):
        self.asctelemetry.finish_task(
            self.current_play,
            'skipped',
            result,
            self._dump_results(result._result)
        )

    def v2_playbook_on_include(self, included_file):
        self.asctelemetry.finish_task(
            self.current_play,
            'included',
            included_file,
            ""
        )

    def v2_playbook_on_stats(self, stats):

        self.asctelemetry.finish_play(self.plays_data, self.current_play)
        self.current_play = None
        
        if self.errors == 0:
            status = Status(status_code=StatusCode.OK)
        else:
            status = Status(status_code=StatusCode.ERROR)
       
        self.asctelemetry.generate_distributed_traces(
            self.ansible_playbook,
            self.plays_data,
            status,
            self.traceparent,
            self.disable_logs,
            self.disable_attributes_in_logs
        )

        if asc_TRACE:
            self.trace_display()

        self._display.display("Ansible Sharp Monitoring and Telemetry callback plugin finished with {0} errors".format(self.errors))

    def v2_runner_on_async_failed(self, result, **kwargs):
        self.errors += 1


    def trace_display(self):
        self._display.banner("TRACE")
        
        for p_uuid, p in self.plays_data.items():
            self._display.display("Play {0}".format(p.name))

            for t_uuid, t in p.tasks.items():
                self._display.display("  - Task {0} . {1}".format(t.action, t.name))

                for h_uuid, h in t.host_data.items():
                    self._display.display("      - Host {0}".format(h.name))
