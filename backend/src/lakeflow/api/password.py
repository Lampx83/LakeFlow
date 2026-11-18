"""Print a bcrypt hash for LAKEFLOW_ADMIN_PASSWORD_HASH (password is read from a prompt, never stored)."""
import getpass

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if __name__ == "__main__":
    print(pwd_context.hash(getpass.getpass("New admin password: ")))
