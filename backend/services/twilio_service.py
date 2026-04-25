from twilio.rest import Client
import os

class TwilioService:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
        )
        self.from_number = os.getenv(
            "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
        )

    def send_whatsapp(self, to: str, body: str) -> str | None:
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                body=body,
                to=to,
            )
            return message.sid
        except Exception as e:
            print(f"[Twilio] Failed to send to {to}: {e}")
            return None


twilio_service = TwilioService()
