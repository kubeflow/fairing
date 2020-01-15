from datetime import datetime
from logging import getLogger
import time

from google.cloud import logging_v2
from googleapiclient import discovery
from googleapiclient import errors

from kubeflow.fairing import utils
from kubeflow.fairing import http_utils
from kubeflow.fairing.deployers.deployer import DeployerInterface
from kubeflow.fairing.cloud.gcp import guess_project_name

logger = getLogger(__name__)

DEFAULT_LOGGING_INTERVAL_TIME_SEC = 30


class GCPJob(DeployerInterface):
    """Handle submitting training job to GCP."""

    def __init__(self, project_id=None, region=None, scale_tier=None,
                 job_config=None, use_stream_logs=False):
        """
        :param project_id: Google Cloud project ID to use.
        :param region: region in which the job has to be deployed.
            Ref: https://cloud.google.com/compute/docs/regions-zones/
        :param scale_tier: machine type to use for the job.
            Ref: https://cloud.google.com/ml-engine/docs/tensorflow/machine-types
        :param job_config: Custom job configuration options. If an option is specified
            in the job_config and as a top-level parameter, the parameter overrides
            the value in the job_config.
            Ref: https://cloud.google.com/ml-engine/reference/rest/v1/projects.jobs
        :param use_stream_logs: If true, when deploying a job, output the job stream
            log until the job ends.
        """
        self._project_id = project_id or guess_project_name()
        self._region = region or 'us-central1'
        self._job_config = job_config or {}
        self.scale_tier = scale_tier
        self._ml = discovery.build('ml', 'v1')
        self._ml._http = http_utils.configure_http_instance(self._ml._http) #pylint:disable=protected-access
        self._use_stream_logs = use_stream_logs

    def create_request_dict(self, pod_template_spec):
        """Return the request to be sent to the ML Engine API.

        :param pod_template_spec: pod spec template of the training job

        """
        # TODO: Update deploy interface to pass image directly instad of
        # PodTemplateSpec.
        # Retrieve image uri from pod template spec.
        image_uri = pod_template_spec.containers[0].image
        self._job_name = 'fairing_job_{}'.format(utils.random_tag())

        # Merge explicitly specified parameters with the job config dictionary
        request_dict = self._job_config
        request_dict['jobId'] = self._job_name
        if 'trainingInput' not in request_dict:
            request_dict['trainingInput'] = {}

        if self.scale_tier:
            request_dict['trainingInput']['scaleTier'] = self.scale_tier

        if 'masterConfig' not in request_dict['trainingInput']:
            request_dict['trainingInput']['masterConfig'] = {}
        request_dict['trainingInput']['masterConfig']['imageUri'] = image_uri

        if self._region:
            request_dict['trainingInput']['region'] = self._region

        return request_dict

    def deploy(self, pod_template_spec):
        """Deploys the training job

        :param pod_template_spec: pod spec template of the training job

        """
        request_dict = self.create_request_dict(pod_template_spec)

        try:
            print('Creating training job with the following options: {}'.format(
                str(request_dict)))
            response = self._ml.projects().jobs().create( #pylint:disable=unused-variable
                parent='projects/{}'.format(self._project_id),
                body=request_dict
            ).execute()
            print('Job submitted successfully.')
            self.get_logs()
            return self._job_name
        except errors.HttpError as err:
            print('There was an error submitting the job.')
            print(err._get_reason()) #pylint:disable=protected-access

    def get_logs(self):
        """Streams the logs for the training job"""
        print('Access job logs at the following URL:')
        print('https://console.cloud.google.com/mlengine/jobs/{}?project={}'
              .format(self._job_name, self._project_id))
        if self._use_stream_logs:
            self.stream_logs()

    def stream_logs(self, interval_time_sec=DEFAULT_LOGGING_INTERVAL_TIME_SEC):
        """Streams the logs for the training job from stackdriver logging

        :param interval_time_sec: the interval time fetching logs.

        """

        # client for fetching logs from stackdriver
        client = logging_v2.LoggingServiceV2Client()
        fetch_with_timestamp_filter = lambda timestamp: client.list_log_entries(
            resource_names=['projects/{}'.format(self._project_id)],
            filter_='resource.labels.job_id="{}" '
                    'timestamp>="{}"'.format(self._job_name, timestamp))

        # request for getting job info
        req = self._ml.projects().jobs().get(name='projects/{}/jobs/{}'.format(
            self._project_id, self._job_name))
        job_info = req.execute()
        last_updated_at = job_info['createTime']
        last_insert_id_set = set()
        finished = False
        try:
            while not finished:
                job_info = req.execute()
                # When `finished` is true, job has been finished. See below for a list of status.
                # https://cloud.google.com/ml-engine/reference/rest/v1/projects.jobs?hl=ja#State
                finished = job_info['state'] in ('SUCCEEDED', 'FAILED', 'CANCELLED')

                # For prevent duplicate logging
                entries = [e for e in fetch_with_timestamp_filter(last_updated_at)
                           if e.insert_id not in last_insert_id_set]
                for entry in entries:
                    # TODO Add custom filtering
                    if 'message' in entry.json_payload.keys():
                        msg = entry.json_payload['message']
                        if msg:
                            logger.info(msg.strip())
                    if entry.text_payload:
                        logger.info(entry.text_payload.strip())
                if entries:
                    # update filtering condition
                    last_updated_at = datetime.utcfromtimestamp(
                        entries[-1].timestamp.seconds).isoformat()
                    last_insert_id_set = set(map(lambda e: e.insert_id, entries))
                if not finished:
                    time.sleep(interval_time_sec)
        finally:
            logger.info('Job has been finished.')
            logger.info(job_info)
