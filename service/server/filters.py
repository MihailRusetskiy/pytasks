from service.server import manager


class Filter:
    def do_filter(self):
        raise NotImplementedError


class AuthFilter(Filter):
    def do_filter(self):
        if 'auth_token' in self.request.headers:
            token = self.request.headers['auth_token'][0]
            for au in manager.Server.context['authorized_users']:
                if au == token:
                    return True
        else: return True

