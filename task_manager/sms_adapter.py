
from .notifier import Notifier
from .external_sms import ExternalSMSService


class SMSAdapter(Notifier):

    def __init__(
        self,
        sms_service: ExternalSMSService,
        phone_number: str
    ):
        self.sms_service = sms_service
        self.phone_number = phone_number

    def send(self, message: str):
        self.sms_service.send_message(
            self.phone_number,
            message
        )
