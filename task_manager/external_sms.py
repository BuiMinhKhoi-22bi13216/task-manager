class ExternalSMSService:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, phone_number, message):
        self.sent_messages.append((phone_number, message))

        print(f"SMS to {phone_number}: {message}")
