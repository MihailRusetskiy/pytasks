from service.utils import rfc1123_datetime_encode
from datetime import datetime
import subprocess
import time


class Job:
    @staticmethod
    def get_job(context, job_id):
        if job_id in [job['job_id'] for job in context['jobs']]:
            for job in context['jobs']:
                if job['job_id'] == job_id:
                    return job
        else:
            return None

    @staticmethod
    def get_jobs(context):
        return context['jobs']

    @staticmethod
    def get_job_status(context, status_id):
        if status_id in [status['status_id'] for status in context['statuses']]:
            for status in context['statuses']:
                if status['status_id'] == status_id:
                    return status
        else:
            return None

    @staticmethod
    def get_job_statuses(context):
        return context['statuses']

    @staticmethod
    def get_job_result(context, result_id):
        if result_id in [result['result_id'] for result in context['results']]:
            for result in context['results']:
                if result['result_id'] == result_id:
                    return result
        else:
            return None

    @staticmethod
    def get_job_results(context):
        return context['results']

    @staticmethod
    def search_job_by_command(context, command_patterns):
        return [job for command_pattern in command_patterns for job in context['jobs']\
                if command_pattern in job['command']]

    @staticmethod
    def add_job(context, command):
        id = (max([job['job_id'] for job in context['jobs']]) if len(context['jobs']) else 0) + 1
        context['jobs'].append({'job_id': id, 'command': command, 'created': rfc1123_datetime_encode(datetime.now())})
        context['statuses'].append({'status_id': id, 'done': False})
        return context

    @staticmethod
    def remove_job(context, job_id):
        if job_id in [job['job_id'] for job in context['jobs']]:
            for job in context['jobs']:  # remove job
                if job['job_id'] == job_id:
                    context['jobs'].remove(job)
            for status in context['statuses']:  # remove status
                if status['status_id'] == job_id:
                    context['statuses'].remove(status)
            return context
        else:
            return None

    @staticmethod
    def remove_job_result(context, job_result_id):
        if job_result_id in [result['result_id'] for result in context['results']]:
            for result in context['results']:  # remove result
                if result['result_id'] == job_result_id:
                    context['results'].remove(result)
            return context
        else:
            return None


class JobExecutor:
    @staticmethod
    def do_job(context, job):
        start_time = time.time()
        command = [task['command'] for task in context['jobs'] if task['job_id'] == job['status_id']][0]
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_ = b' '.join(p.stdout.readlines()).decode('utf-8')
        stderr_ = b' '.join(p.stderr.readlines()).decode('utf-8')
        retval = p.wait()
        duration = time.time() - start_time
        context['results'].append({'result_id': job['status_id'], 'duration': duration, \
                           'completed': rfc1123_datetime_encode(datetime.now()), 'stdout': stdout_,\
                           'stderr': stderr_, 'exit_code': retval})
        for job_status in context['statuses']:
            if job_status['status_id'] == job['status_id']:
                context['statuses'].remove(job_status)
        context['statuses'].append({'status_id': job['status_id'], 'Location': '/api/results/{}'.format(job['status_id'])})
