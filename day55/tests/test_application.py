from customer_support.application import SupportApplication
from customer_support.assistant import SupportAnswer
from customer_support.conversation import History


class RecordingAssistant:
    def __init__(self):
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        return SupportAnswer(question, ())


def test_conversation_is_on_the_product_path():
    assistant = RecordingAssistant()
    app = SupportApplication(assistant, History(max_turns=2))

    app.ask("退款多久到账？", session_id="s1")
    app.ask("那发票呢？", session_id="s1")

    assert assistant.questions[-1] == "上一问题：退款多久到账？\n当前追问：那发票呢？"
