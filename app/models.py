from app import app, db
from Crypto.Cipher import AES
from Crypto import Random

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200))
    teams = db.relationship("Team", backref="user", lazy=True)

    def __init__(self, username, password=None):
        self.username = username
        self.password = User.encrypt_password(password) if password else None

        user = User.query.filter_by(username=username).first()
        self.is_matching_password = user != None and password == User.decrypt_password(user.password)


    def __repr__(self):
        return "<User %s>" % self.username

    @property
    def is_authenticated(self):
        return self.id != None or (self.is_active and self.is_matching_password)

    @property
    def is_active(self):
        return self.password != None and self.password != ""

    @property
    def is_anonymous(self):
        return not self.is_authenticated

    def get_id(self):
        return str(self.id).decode("utf-8")

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

class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    external_id = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return "<Team (%s, %s, %s)>" % (self.name, self.external_id, self.user.username)
