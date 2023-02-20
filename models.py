from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import time
from werkzeug.security import generate_password_hash, check_password_hash
flask_app = Flask(__name__)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/flask'
flask_app.config['SECRET_KEY'] = "b'{\x1f*!\xf3p\xc6\xae\xf0\x08\xa8~'"
from datetime import datetime,timedelta
db = SQLAlchemy(flask_app)

import enum
class PostionTypeEnum(enum.Enum):
    admin = 'admin'
    receptionist = 'receptionist'
    customer='customer'
class User(db.Model):
    __tablename__ = 'user'
    id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    username=db.Column(db.String(64), nullable=False,unique=True)
    password=db.Column(db.String(500), nullable=False)
    phone=db.Column(db.String(64), nullable=False, unique=True)
    email=db.Column(db.String(64), nullable=False, unique=True)
    position_type= db.Column(db.Enum(PostionTypeEnum), default=PostionTypeEnum.customer,nullable=False)
    hashCode = db.Column(db.String(400))
    def set_password(self, password):
        self.password= generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password ,password)

  
    def __repr__(self):
        return f'<User {self.username}>'
    def to_json_user(self):
      return {
      'id':self.id,
      'username': self.username,
      'password': self.password,
      'phone': self.phone,
      'email': self.email,
      'position_type': self.position_type,
      }


class Employee(db.Model):
    __tablename__ = 'employee'
    emp_id =db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    address=db.Column(db.String(100), nullable=False)
    qualification=db.Column(db.String(100),nullable=True)
    age=db.Column(db.Integer,nullable=True)
    userId=db.Column(db.Integer, db.ForeignKey('user.id'))
    def to_json_employee(self):
      return {
      'emp_id':self.emp_id,
      'address': self.address,
      'qualification': self.qualification,
      'age': self.age,
      'UserId': self.userId 
      }


class Customer(db.Model):
    __tablename__ = 'customer'
    cust_id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    address=db.Column(db.String(500),nullable=True)
    age=db.Column(db.Integer,nullable=True)
    userId=db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Customer {self.id}>'
    def to_json_customer(self):
      return {
      'cust_id':self.cust_id,
      'address': self.address,
      'age': self.age,
      'UserId': self.userId 
      }

class Room(db.Model):
    __tablename__ = 'room'
    id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    type=db.Column(db.String(64), nullable=False)
    price=db.Column(db.Integer, nullable=False)
    status=db.Column(db.String(64), nullable=False)
    userId=db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Room {self.id}>'
    def to_json_room(self):
      return {
      'id':self.id,
      'type': self.type,
      'price': self.price,
      'status': self.status,
    #   'UserId': self.userId 
      }

class Booking(db.Model):
    __tablename__ = 'booking'

    id=db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    starting_date=db.Column(db.DateTime)
    releaving_date=db.Column(db.String(64), nullable=False)
    no_of_person=db.Column(db.Integer, nullable=False)
    userId=db.Column(db.Integer, db.ForeignKey('user.id'))
    roomId=db.Column(db.Integer, db.ForeignKey('room.id')) 

    def __repr__(self):
        return f'<Booking {self.id}>'
    def to_json_booking(self):
      return {
      'id':self.id,
      'starting_date': self.starting_date,
      'releaving_date': self.releaving_date,
      'no_of_person': self.no_of_person,
      'UserId': self.userId ,
      'roomId': self.roomId 
      }

