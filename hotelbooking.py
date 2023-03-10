from models import db,flask_app
from models import *

import datetime
from celery import Celery
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import create_access_token,create_refresh_token
jwt = JWTManager(flask_app)

from flask_mail import Mail, Message

# configuration of mail
flask_app.config['MAIL_SERVER']='smtp.gmail.com'
flask_app.config['MAIL_PORT'] = 465
flask_app.config['MAIL_USERNAME'] = 'shisirakrishna@gmail.com'
flask_app.config['MAIL_PASSWORD'] = 'czoeidbwdzxggnqr'   #2 step verification password
flask_app.config['MAIL_USE_TLS'] = False
flask_app.config['MAIL_USE_SSL'] = True

# Initialize extensions
mail = Mail(flask_app)

from datetime import timedelta
from celery.schedules import crontab
celery_app = Celery('hotelbooking', broker='redis://localhost')
celery_app.conf.beat_schedule = {
    "see-you-in-ten-seconds-task": {
        "task": "hotelbooking.see_you",
        "schedule": 10.0
    }
}

@celery_app.task
def see_you():
    print("See you in ten seconds!")
    print("beat is working:")

@celery_app.task
def send_async_email(email_data):
    """Background task to send an email with Flask-Mail."""
    msg = Message(email_data['subject'],
                  sender="shisirakrishn@gmail.com",
                  recipients=[email_data['to']])
    msg.body = email_data['body']
    with flask_app.app_context():
        mail.send(msg)

@flask_app.route('/register', methods = [ 'POST'])
def Register():
   
    try:
        if request.method == 'POST':
            id=request.json['id']
            username=request.json['username']
            password=request.json['password']
            phone=request.json['phone']
            email=request.json['email']
            position_type=request.json['position_type']
            us_obj= User.query.filter_by(username=username).first()
            user_by_email = User.query.filter_by(email=email).first()
            user_by_id= User.query.filter_by(id=id).first()
            print("us_obj---------------",us_obj)
            print("user_by_id============",user_by_id)
            print("user_by_email=============",user_by_email)
            if us_obj or user_by_email:
                return[{"msg" : 'Error: User exists!'}]
            elif user_by_id:
                return[{"msg" : 'Error:User with same Id exists!'}]
            else:
                user_obj=User(id=id,username=username,phone=phone,email=email,position_type=position_type)
                user_obj.set_password(password)
                user_obj.hashCode=None
                # msg=Message(
                #     'Hello',
                #     sender="shisirakrishna@gmail.com",
                #     recipients=[email]   
                # )
                # msg.body="Hello Flask message sent from Flask-Mail"
                # mail.send(msg)

                email_data = {
                'subject': 'HotelBooking Registration ',
                'to': email,
                'body': 'You are successfully registeded.'}
                send_async_email.delay(email_data)
                db.session.add(user_obj)
                db.session.commit()
            print('Record was successfully added')
            return jsonify({
                'id':id,
                'username':username,
                'password':user_obj.password,
                'phone':phone,
                'email':email,
                'position_type':position_type
                })
    except Exception as error:
            print("\nException Occured", error)
        

@flask_app.route('/login', methods=['POST'])
def login():
    try:
        username = request.json.get("username")
        password = request.json.get("password")
        user = User.query.filter_by(username = username).one_or_none()
        if user is not None and check_password_hash(user.password, password):
            ret = {
                'access_token': create_access_token(identity=username),
                'refresh_token': create_refresh_token(identity=username)
            }
            return jsonify(ret), 200
        else:
            return jsonify(message='login failed'), 401
    except Exception as error:
            print("\nException Occured", error)
@flask_app.route("/refresh", methods=["GET"])
@jwt_required()
def refresh():
    current_user = get_jwt_identity()
    # refresh_token=request.json.get("refresh_token")
    print("current_user",current_user)
    ret = {
        'access_token': create_access_token(current_user)
    }
    return jsonify(ret), 200
  
@flask_app.route("/currentuser", methods=["GET"])
@jwt_required()
def protected1():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


import random
import string
@flask_app.route('/forgotpassword',methods=["POST"])
def index():
    if request.method=="POST":
        email=request.json['email']
        # email = request.form['email']
        check = User.query.filter_by(email=email).first()
        if check:
            hashCode = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
            check.hashCode = hashCode
            db.session.commit()
            msg = Message('Confirm Password Change', sender = 'shisirakrishna@gmail.com', recipients = [email])
            msg.body = "Hello,\nWe've received a request to reset your password. If you want to reset your password, click the link below and enter your new password\n http://192.168.68.129:5000/" + check.hashCode
            mail.send(msg)
            return "check your mail"
        else:
            return "invalid email"  
    
@flask_app.route("/<string:hashCode>",methods=["GET","POST"])

def hashcode(hashCode):
    check = User.query.filter_by(hashCode=hashCode).first()    
    if check:
        if request.method == 'POST':
            passw = request.form['passw']
            cpassw = request.form['cpassw']
            if passw == cpassw:
                # check.password = passw
                check.hashCode= None
                check.set_password(passw)
                db.session.commit()
                return "changed"
            else:
                return 'password mismatch'
                return '''
                     <form method="post">
                       <small>enter your new password</small> <br>
                     <input type="password" name="passw" id="passw" placeholder="password"> <br>
                        <input type="password" name="cpassw" id="cpassw" placeholder="confirm password"> <br>
                         <input type="submit" value="Submit">
                    </form>
                 '''
              
        else:
            return '''
                <form method="post">
                    <small>enter your new password</small> <br>
                    <input type="password" name="passw" id="passw" placeholder="password"> <br>
                    <input type="password" name="cpassw" id="cpassw" placeholder="confirm password"> <br>
                    <input type="submit" value="Submit">
                </form>
            '''
    else:
        return "Time is exceed."
@flask_app.route('/employee/add', methods = ['GET', 'POST'])
@jwt_required()
def employee_add():
    current_user= get_jwt_identity()
    print("----------current_user-------------",current_user)
    user_obj = User.query.filter_by(username=current_user).first()
    print("---------user_obj----------",user_obj.email)
    print("--------------",user_obj.position_type)
    list=[]
    posi_type=str(user_obj.position_type)
    list = posi_type.split(".")
    role=list[1]
    print("-----------------role-----------------",role)
    if request.method=='GET':
        emp_objs= Employee.query.all()
        return jsonify([emp_obj.to_json_employee() for emp_obj in emp_objs])
    if request.method == 'POST':
       
        if role in 'admin':
            
            emp_id=request.json['emp_id']
            address=request.json['address']
            qualification=request.json['qualification']
            age=request.json['age']
            userId=request.json['userId']
            emp_obj=Employee(emp_id=emp_id,address=address,qualification=qualification,age=age,userId=userId)
            em_obj = User.query.filter_by(id=userId).first()
            db.session.add(emp_obj)
            db.session.commit()
            return jsonify({
            'emp_id':emp_id,
            'address':address,
            'qualification':qualification,
            'age':age,
            'admin_name':user_obj.username,
            'emp_name':em_obj.username
            })
        else:
            return jsonify({"output":"Admin can only add the Employee"})



@flask_app.route('/employee/update/<int:id>',methods=['GET','POST'])
@jwt_required()
def employee_update(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        print("-----------------role-----------------",role)
        emp_obj = Employee.query.filter_by(emp_id=id).first()
        if request.method=='GET':
            if emp_obj:
                 return jsonify([emp_obj.to_json_employee()])
            else:
                    return jsonify({"output":"employee not found"})
        if request.method == 'POST':
            if role in 'admin':
                if emp_obj:
                    emp_obj.emp_id=request.json['emp_id']
                    print("em---",emp_obj.address)
                    emp_obj.address=request.json.get("address")
                    emp_obj.qualification=request.json.get("qualification")
                    emp_obj.age=request.json.get("age")
                    print("-----------userid--------",emp_obj.userId)
                    emp_obj.userId=request.json.get("userId")
                    db.session.add(emp_obj)
                    db.session.commit()
                    print('Record was successfully added')
                    return jsonify({
                    'emp_id':emp_obj.emp_id,
                    'address':emp_obj.address,
                    'qualificatin':emp_obj.qualification,
                    'age':emp_obj.age,
                    'userId':emp_obj.userId
                    })
                else:
                    return jsonify({"output":"employee not found"})
                   
            else:
                return jsonify({"output":"Admin can only update the Employee"})  
    except Exception as error:
        print("Error while updating PostgreSQL table", error)

@flask_app.route('/employee/delete/<int:id>',methods=['GET'])
@jwt_required()
def employee_delete(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        emp_obj = Employee.query.filter_by(emp_id=id).first()
        if request.method == 'GET':
            if role in 'admin':
                if emp_obj:
                    db.session.delete(emp_obj)
                    db.session.commit()
                    return jsonify({"output":"deleted"})
                else:
                    return jsonify({"output":"employee  not found"})
            else:
                return jsonify({"output":"Admin can only delete the Employee"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)

@flask_app.route('/customer/add', methods = ['GET', 'POST'])
@jwt_required()
def customer_add():
    current_user= get_jwt_identity()
    print("----------current_user-------------",current_user)
    user_obj = User.query.filter_by(username=current_user).first()
    print("---------user_obj----------",user_obj.email)
    print("--------------",user_obj.position_type)
    list=[]
    posi_type=str(user_obj.position_type)
    list = posi_type.split(".")
    role=list[1]
    print("-----------------role-----------------",role)
    if request.method=='GET':
        cust_objs= Customer.query.all()
        return jsonify([cust_obj.to_json_customer() for cust_obj in cust_objs])
    if request.method == 'POST': 
        if role in 'receptionist':
            cust_id=request.json['cust_id']
            address=request.json['address']
            age=request.json['age']
            userId=request.json['userId']
            cust_obj=Customer(cust_id=cust_id,address=address,age=age,userId=userId)
            cu_obj = User.query.filter_by(id=userId).first()
            db.session.add(cust_obj)
            db.session.commit()
            return jsonify({
            'cust_id':cust_id,
            'address':address,
            'age':age,
            'receptionist_name':user_obj.username,
            'emp_name':cu_obj.username
            })
        else:
            return jsonify({"output":"receptionist can only add the Customer"})


@flask_app.route('/customer/update/<int:id>',methods=['GET','POST'])
@jwt_required()
def customer_update(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        cust_obj = Customer.query.filter_by(cust_id=id).first()
        if request.method=='GET':
            if cust_obj:
                return jsonify([cust_obj.to_json_customer()])
            return jsonify({"output":" Employee not found"})
        if request.method == 'POST':
            if role in 'receptionist':
                if cust_obj:
                    cust_obj.cust_id=request.json['cust_id']
                    print("em---",cust_obj.address)
                    cust_obj.address=request.json.get("address")
                    cust_obj.age=request.json.get("age")
                    cust_obj.userId=request.json.get("userId")
                    db.session.add(cust_obj)
                    db.session.commit()
                    print('Record was successfully added')
                    return jsonify({
                    'cust_id':cust_obj.cust_id,
                    'address':cust_obj.address,
                    'age':cust_obj.age,
                    'userId':cust_obj.userId
                    })
                else:
                    return jsonify({"output":"customer not found"})
            else:
                return jsonify({"output":"Receptionist can only update the customer"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/customer/delete/<int:id>',methods=['GET'])
@jwt_required()
def customer_delete(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        cust_obj = Customer.query.filter_by(cust_id=id).first()
        if request.method == 'GET':
            if role in 'receptionist':
                if cust_obj:
                    db.session.delete(cust_obj)
                    db.session.commit()
                
                    return jsonify({"output":"deleted"})
                else:
                    return jsonify({"output":"customer not found"})
            else:
                return jsonify({"output":"Receptionist can only delete the Customer"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/room/available',methods=['GET'])
def room_available():
    if request.method=='GET':
        room_objs= Room.query.all()
        return jsonify([room_obj.to_json_room() for room_obj in room_objs if room_obj.status == "not booked"])

@flask_app.route('/room/add', methods = ['GET', 'POST'])
@jwt_required()
def room_add():
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        if request.method=='GET':
            room_objs= Room.query.all()
            print(room_objs)
            return jsonify([room_obj.to_json_room() for room_obj in room_objs])
            
        if request.method == 'POST':
            if role in 'admin':
                id=request.json['id']
                type=request.json['type']
                price=request.json['price']
                status=request.json['status']
                # userId=request.json['userId']
                userId=user_obj.id
                room_obj=Room(id=id,type=type,price=price,status=status,userId=userId)
                db.session.add(room_obj)
                db.session.commit()
                print('Record was successfully added')
                return jsonify({
                'id':id,
                'type':type,
                'price':price,
                'status': status
                # 'Admin_userId':userId
                    })
            else:
                return jsonify({"output":"Admin can only add the Room"})       
    except  Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/room/update/<int:id>',methods=['GET','POST'])
@jwt_required()
def room_update(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        room_obj = Room.query.filter_by(id=id).first()
        if request.method=='GET':
            if room_obj:
                return jsonify([room_obj.to_json_room() ])
            else:
                return jsonify({"output":"room not found"})
        if request.method == 'POST':
            if role in 'admin':
                if room_obj:
                    room_obj.id=request.json['id'],
                    room_obj.type=request.json['type'],
                    room_obj.price=request.json['price'],
                    room_obj.status=request.json['status'],
                    room_obj.userId=user_obj.id,
                    db.session.add(room_obj)
                    db.session.commit()
                    print('Record was successfully added')
                    return jsonify({
                    'id':room_obj.id,
                    'type':room_obj.type,
                    'price':room_obj.price,
                    'status': room_obj.status
                    
                    })
                else:
                    return jsonify({"output":"room not found"})
            else:
                return jsonify({"output":"Admin can only update the Room"})     
    except Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/room/delete/<int:id>',methods=['GET'])
@jwt_required()
def room_delete(id):
    try:
        current_user= get_jwt_identity()
        user_obj = User.query.filter_by(username=current_user).first()
        list=[]
        posi_type=str(user_obj.position_type)
        list = posi_type.split(".")
        role=list[1]
        room_obj = Room.query.filter_by(id=id).first()
        if request.method == 'GET':
            if role in 'admin':
                if room_obj:
                    db.session.delete(room_obj)
                    db.session.commit()
                
                    return jsonify({"output":"deleted"})
                else:
                    return jsonify({"output":"room not found"})
            else:
                return jsonify({"output":"Admin can only update the Room"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)

@flask_app.route('/booking/add', methods = ['GET', 'POST'])
def booking_add():
    try:
        if request.method=='GET':
            booking_objs= Booking.query.all()
            return jsonify([booking_obj.to_json_booking() for booking_obj in booking_objs])
        if request.method == 'POST':
            id=request.json['id']
            starting_date=request.json['starting_date']
            releaving_date=request.json['releaving_date']
            no_of_person=request.json['no_of_person']
            userId=request.json['userId']
            roomId=request.json['roomId']
            booking_obj=Booking(id=id,starting_date=starting_date,releaving_date=releaving_date,no_of_person=no_of_person,userId=userId,roomId=roomId)
            db.session.add(booking_obj)
            db.session.commit()
            room_obj= Room.query.filter_by(id=roomId).first()
            room_obj.status="booked"
            print(room_obj)
            db.session.add(room_obj)
            db.session.commit()
            print('Record was successfully added')
            return jsonify({
            'id':id,
            'starting_date':starting_date,
            'releaving_date':releaving_date,
            'no_of_person':no_of_person,
            'userId':userId,
            'roomId':roomId
            })
    except Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/booking/update/<int:id>',methods=['GET','POST'])
def booking_update(id):
    try:
        booking_obj = Booking.query.filter_by(id=id).first()
        if request.method=='GET':
            if booking_obj:
                return jsonify([booking_obj.to_json_booking()])
            else:
                return jsonify({"output":"booking id is not found"})
        if request.method == 'POST':
            print("-----------------------------",booking_obj)
            if booking_obj:
                id=request.json['id']
                starting_date=request.json['starting_date']
                releaving_date=request.json['releaving_date']
                no_of_person=request.json['no_of_person']
                userId=request.json['userId']
                roomId=request.json['roomId']
                booking_obj.id=id,
                booking_obj.starting_date=starting_date,
                booking_obj.releaving_date=releaving_date,
                booking_obj.no_of_person=no_of_person,
                booking_obj.userId=userId,
                booking_obj.roomId=roomId
                db.session.add(booking_obj)
                db.session.commit()
                print('Record was successfully updated')
                return jsonify({
                'id':id,
                'starting_date':starting_date,
                'releaving_date':releaving_date,
                'no_of_person':no_of_person,
                'userId':userId,
                'roomId':roomId
                })
            else:
                return jsonify({"output":"booking id is not found"})          
    except Exception as error:
        print("Error while updating PostgreSQL table", error)

@flask_app.route('/booking/delete/<int:id>',methods=['GET'])
def booking_delete(id):
    try:
        booking_obj = Booking.query.filter_by(id=id).first()
        if request.method == 'GET':
            if booking_obj:
                id=booking_obj.id
                db.session.delete(booking_obj)
                db.session.commit()
                room_obj= Room.query.filter_by(id=id).first()
                room_obj.status="not booked"
                print(room_obj)
                db.session.add(room_obj)
                db.session.commit()
                return jsonify({"output":"deleted"})
            else:
                return jsonify({"output":" not found"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)


@flask_app.route('/user/delete/<int:id>',methods=['GET'])
def user_delete(id):
    try:
        user_obj = User.query.filter_by(id=id).first()
        print(user_obj)
        if request.method == 'GET':
            if user_obj:
                db.session.delete(user_obj)
                db.session.commit()
                return jsonify({"output":"deleted"})
            else:
                return jsonify({"output":"user not found"})
    except Exception as error:
        print("Error while updating PostgreSQL table", error)

@flask_app.route('/') 
def show_all():
   return jsonify({ 
        'status': 'Data is posted to PostgreSQL!',})

if __name__ == '__main__': 
    with flask_app.app_context():
   
   #  db.create_all()
      db.create_all()
      flask_app.run(host='192.168.68.129' ,port=5000,debug = True)


# redis-server
# celery -A hotelbooking  worker --loglevel=INFO
# celery -A hotelbooking  beat --loglevel=INFO
# python3 hotelbooking.py
#  kill -9 $(lsof -t -i:"5000")