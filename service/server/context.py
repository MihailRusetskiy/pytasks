class Context:
    def __init__(self):
        self.context = self.init_context_data()

    def __get__(self, instance, owner):
        return self.context

    def __set__(self, instance, value):
        self.context = value

    def init_context_data(self):
        authorized_users = []
        authorized_users.append('test_token')
        return {'jobs': [], 'statuses': [], 'results': [], 'authorized_users': authorized_users}
