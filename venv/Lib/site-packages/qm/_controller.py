class Controller(object):
    def __init__(self, controller_name):
        self.name = controller_name

    @staticmethod
    def build_from_message(message):
        return Controller(message.name)
