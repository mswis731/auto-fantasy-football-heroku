from app import app, db
from Crypto.Cipher import AES
from Crypto import Random

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200))

    def __init__(self, username, password):
        self.username = username
        self.password = User.encrypt_password(password)

    def __repr__(self):
        return '<User %r>' % self.username

    @staticmethod
    def encrypt_password(plaintext):
        key = app.config["SECRET_KEY"]
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        hash = (iv + cipher.encrypt(plaintext)).encode("hex")
        return hash

    @staticmethod
    def decrypt_password(hash):
        key = app.config["SECRET_KEY"]
        cipher = AES.new(key, AES.MODE_CFB, "0"*AES.block_size)
        plaintext = cipher.decrypt(hash.decode("hex"))[AES.block_size:]
        return plaintext
