import tidalapi


class State:
    IDLE = "idle"
    LOGGING_IN = "logging_in"
    LOGGED_IN = "logged_in"
    FAILED = "failed"


class TidalClient:
    def __init__(self):
        self.session = tidalapi.Session()
        self.logged_in = False
        self.state = State.IDLE

    def login(self):
        self.state = State.LOGGING_IN
        try:
            result = self.session.login_oauth_simple()

            if result is None:
                print("Already logged in or login not required")
                self.logged_in = self.is_logged_in()
                return

            if isinstance(result, tuple) and len(result) == 2:
                _, future = result
                future.result(timeout=300)
            else:
                raise Exception(f"Unexpected result from login_oauth_simple: {result}")

            if not self.is_logged_in():
                raise Exception("Login succeeded but session is not valid")

            self.logged_in = True
            self.state = State.LOGGED_IN
            print("Login successful")

        except Exception as exc:
            print(f"Login failed: {exc}")
            self.logged_in = False
            self.state = State.FAILED

    def is_logged_in(self):
        return self.session.check_login()

    def _require_login(self):
        if not self.is_logged_in():
            raise Exception("Not logged in")

    def get_username(self):
        self._require_login()
        return self.session.user.username

    def get_user_id(self):
        self._require_login()
        return self.session.user.id
