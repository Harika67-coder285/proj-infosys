from .models import Chat, Message

def send_message(freelancer_id, recruiter_id, sender_id, text):
    chat, _ = Chat.objects.get_or_create(
        freelancer_id=freelancer_id,
        recruiter_id=recruiter_id
    )

    Message.objects.create(
        chat=chat,
        sender_id=sender_id,
        text=text
    )
