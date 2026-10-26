class ExternalSMSService:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    def send_message(self, phone_number: str, message: str) -> None:
        self.sent_messages.append((phone_number, message))
        print(f"SMS to {phone_number}: {message}")