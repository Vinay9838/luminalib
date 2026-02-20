import logging
import jwt

logger = logging.getLogger(__name__)

class BaseJWTValidator:

    HS256: str = 'HS256'
    RS256: str = 'RS256'

    algorithm: str | None = None

    required_claims_mapping: dict = {}

    def __init__(
            self,
            secret_key: str = '',
            public_key: str = '',
            private_key: str = '',
            verify_exp: bool = True,
        ):
        self.secret_key = secret_key
        self.public_key = public_key
        self.private_key = private_key
        self.verify_exp = verify_exp
        if self.secret_key:
            self.algorithm = self.HS256
        elif self.public_key:
            self.algorithm = self.RS256
        
        if not self.algorithm:
            raise ValueError('cONFIGURATION ERROR: No secret or public key provided for JWT validation')
        
    
    def __call__(self, jwt_token: str) -> dict | None:
        return self.decode_token(jwt_token)
        

    def decode_token(self, jwt_token: str) -> dict | None:
        try:
            decoded_payload = jwt.decode(
                jwt=jwt_token,
                key=self.secret_key or self.public_key,
                algorithms=[self.algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': self.verify_exp,
                    'require': self.required_claims_mapping.values(),
                }
            )
        except jwt.ExpiredSignatureError as err:
            logger.warning(f'JWT token expired: {err}')
            return None
        except (jwt.InvalidTokenError, ValueError) as err:
            logger.warning(f'Invalid JWT token: {err}')
            return None
        else:
            return self._process_decoded_payload(decoded_payload)
        
    
    def encode_token(self, **payload) -> str:
        processed_payload = self._process_payload(payload)
        return jwt.encode(
            payload=processed_payload,
            key=self.secret_key if self.algorithm == self.HS256 else self.private_key,
            algorithm=self.algorithm,
        )

    def _process_decoded_payload(self, decoded_payload: dict) -> dict:
        if self.required_claims_mapping:
            return {
                claim: decoded_payload[key]
                for key, claim in self.required_claims_mapping.items()
            }
        else:
            return decoded_payload
        
    def _process_payload(self, payload: dict) -> dict:
        if self.required_claims_mapping:
            return {
                key: payload[claim]
                for claim, key in self.required_claims_mapping.items()
            }
        else:
            return payload