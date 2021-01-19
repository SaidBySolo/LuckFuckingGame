from hashlib import sha256
from hmac import new
from secrets import token_hex


class RolledData:
    def __init__(self, roll: int, nonce: int, server_seed_hash: str,
                 client_seed: str):
        self.roll = roll
        self.nonce = nonce
        self.server_seed_hash = server_seed_hash
        self.client_seed = client_seed


class ProvablyFair:
    def __init__(
            self,
            client_seed: str = None,
            server_seed: str = None,
            nonce: int = 0,
            last_rolled_data=None,
    ) -> None:
        self.client_seed = client_seed or token_hex(20)
        self.nonce = nonce
        self.server_seed, self.server_seed_hash = (
            self.hash_server_seed(server_seed)
            if server_seed else self.generate_server_seed())
        self.last_rolled_data = last_rolled_data

    @classmethod
    def verify_roll(cls, server_seed: str, rolled_data: RolledData):
        pf_instance = cls(rolled_data.client_seed, server_seed=server_seed)

        pf_instance_roll = pf_instance.roll(nonce=rolled_data.nonce)
        pf_instance_data = pf_instance.last_rolled_data

        try:
            assert pf_instance.server_seed == server_seed
            assert pf_instance.server_seed_hash == rolled_data.server_seed_hash
            assert pf_instance_data.nonce == rolled_data.nonce
            assert pf_instance_data.roll == rolled_data.roll == pf_instance_roll
        except AssertionError:
            return False

        return True

    @staticmethod
    def generate_server_seed():
        server_seed = token_hex(20)
        server_seed_hash_object = sha256(server_seed.encode())
        server_seed_hash = server_seed_hash_object.hexdigest()
        return server_seed, server_seed_hash

    @staticmethod
    def hash_server_seed(server_seed: str):
        server_seed_hash_object = sha256(server_seed.encode())
        server_seed_hash = server_seed_hash_object.hexdigest()
        return server_seed, server_seed_hash

    def roll(self, nonce: int = None):
        hmac_object = new(
            self.server_seed.encode(),
            f"{self.client_seed}-{nonce or self.nonce}".encode(),
            sha256,
        )
        hmac_hash = hmac_object.hexdigest()

        count = 0

        while True:
            roll_number_str = hmac_hash[count:count + 5]
            roll_number = int(roll_number_str, 16)
            if roll_number > 999_999:
                count += 5
            else:
                break

        self.last_rolled_data = RolledData(roll_number, self.nonce,
                                           self.server_seed_hash,
                                           self.client_seed)

        return roll_number
