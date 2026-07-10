from enum import StrEnum


class DialogEventType(StrEnum):
    MESSAGE_SENT = "message.sent"
    DIALOG_READ = "dialog.read"
