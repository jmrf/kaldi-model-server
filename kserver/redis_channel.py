import json
import time

import redis


class Timer(object):
    """http://www.huyng.com/posts/python-performance-analysis/"""

    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()
        self.secs = self.end_time - self.start_time
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print("elapsed time: %f ms" % self.msecs)

    def current_secs(self):
        self.stop()
        return self.secs


class ASRRedisClient:
    def __init__(self, host="localhost", channel="asr", record_message_history=False):
        self.red = redis.StrictRedis(host=host)
        self.channel = channel
        self.timer_started = False
        self.timer = Timer()
        self.record_message_history = record_message_history
        self.last_message_time = 0.0

        # if record_message_history= True, we store a program in self.message_trace that when
        # executed replays all messages into the asr channel

        self.message_trace = (
            "import time\n"
            "import json\n"
            "import redis\n\n"
            "red = redis.StrictRedis(host=%s)\n"
            "time_factor = 1.0\n"
            'asr_channel = "%s"\n\n' % (host, channel)
        )

    def publish(self, data):
        json_dumps_data = json.dumps(data)
        self.red.publish(self.channel, json_dumps_data)
        cur_time = float(self.timer.current_secs())
        delta = cur_time - self.last_message_time
        self.last_message_time = cur_time
        if self.record_message_history:
            self.message_trace += "time.sleep(%f*time_factor)\n" % delta
            self.message_trace += (
                "red.publish(asr_channel, json.dumps(" + json_dumps_data + "))\n"
            )
            self.message_trace += "print(" + json_dumps_data + ")\n"

    def checkTimer(self):
        if not self.timer_started:
            self.timer.start()
            self.timer_started = True

    def resetTimer(self):
        self.timer_started = False
        self.timer.start()

    def partialUtterance(self, utterance, key="none", speaker="Speaker"):
        self.checkTimer()
        data = {
            "handle": "partialUtterance",
            "utterance": utterance,
            "key": key,
            "speaker": speaker,
            "time": float(self.timer.current_secs()),
        }
        self.publish(data)

    def completeUtterance(self, utterance, confidences, key="none", speaker="Speaker"):
        self.checkTimer()
        data = {
            "handle": "completeUtterance",
            "utterance": utterance,
            "confidences": confidences,
            "key": key,
            "speaker": speaker,
            "time": float(self.timer.current_secs()),
        }
        self.publish(data)

    def asr_loading(self, speaker):
        self.checkTimer()
        data = {
            "handle": "asr_loading",
            "time": float(self.timer.current_secs()),
            "speaker": speaker,
        }
        self.publish(data)

    def asr_ready(self, speaker):
        self.checkTimer()
        data = {
            "handle": "asr_ready",
            "time": float(self.timer.current_secs()),
            "speaker": speaker,
        }
        self.publish(data)

    def sendstatus(self, isDecoding, shutdown=False):
        self.checkTimer()
        data = {
            "handle": "status",
            "time": float(self.timer.current_secs()),
            "isDecoding": isDecoding,
            "shutdown": shutdown,
        }
        self.red.publish(self.channel, json.dumps(data))
