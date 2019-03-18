#!/Users/harmtemolder/miniconda3/envs/assistant-sdk-python/bin/python

# Imports from executables:
# from googlesamples.assistant.grpc.audio_helpers import main
# from googlesamples.assistant.grpc.devicetool import main
# from googlesamples.assistant.library.hotword import main
# from googlesamples.assistant.grpc.pushtotalk import main

"""My first attempt at building a Google Assistant. Im basing myself on
Google's pushtotalk SampleAssistant.
"""

import concurrent.futures
import logging
import tenacity

import grpc

from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2_grpc
from googlesamples.assistant.grpc import assistant_helpers

class TypeAssistant(object):
    """A simple Google Assistant that communicates (in & out) through
    type (instead of through speech).

    :param language_code: language the requests sent to the Assistant are
        written in
    :param device_model_id: identifier of the device model.
    :param device_id: identifier of the registered device instance.
    :param channel: authorized gRPC channel for connection to the Google
        Assistant API.
    :param deadline_sec: gRPC deadline in seconds for Google Assistant API
        call.
    :param device_handler: callback for device actions.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 channel, deadline_sec, device_handler):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id

        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel)
        self.deadline = deadline_sec

        self.device_handler = device_handler

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            # This should let all errors through, according to
            # https://effbot.org/zone/python-with-statement.htm
            return False

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @tenacity.retry(
        # If assist() fails because grpc is unavailable,
        # then retry 2 more times
        reraise=True,
        stop=tenacity.stop_after_attempt(3),
        retry=tenacity.retry_if_exception(is_grpc_error_unavailable))
    def assist(self):
        """Send a typed request to the Assistant and playback the
        response.

        :return: True if conversation should continue.
        """

        continue_conversation = False
        device_actions_futures = []

        logging.info('Expecting typed request.')

        def iter_log_assist_requests():
            for c in self.gen_assist_requests():
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            logging.debug('Reached end of AssistRequest iteration.')

