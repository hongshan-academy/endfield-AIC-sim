from typing import Set


class BaseComponent(object):
    def __init__(self) -> None:
        pass

    def _phase_1_request(self, path: Set["BaseComponent"]):
        # 1. cycle detection
        # 2. check if self.want-to-push
        raise NotImplementedError

    def _phase_2_response(self):
        # 1. visited check
        # 2. has-item + downstream-ready -> send_response_ack
        raise NotImplementedError

    def _phase_3_compute(self):
        pass

    def _phase_4_update(self):
        pass

    def _send_approve(self):
        pass