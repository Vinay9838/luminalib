from drf_spectacular.extensions import OpenApiAuthenticationExtension


class OpenApiTokenAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'userapp.authentication.TokenAuthentication'
    name = 'tokenAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-JWT-Assertion',
            'description': 'JWT token for authentication. Use the token string in the X-JWT-Assertion header.'
        }