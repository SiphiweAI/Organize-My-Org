from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, aliased
import enum

# Define the database URL (SQLite in this case)
DATABASE_URL = "sqlite:///church.db"

# Create an engine and connect to the database
engine = create_engine(DATABASE_URL, echo=True)

# Define a base class for models
Base = declarative_base()

###################################################################

"""Define enumerations"""
class Gender(enum.Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"

# might not be necessary, client will decide
class MembershipStatus(enum.Enum):
    Active = "Active"
    Inactive = "Inactive"

class Marital_Status(enum.Enum):
    Married = "Married"
    Never_Married = "Never Married"
    Divorced = "Divorced"
    Widowed = "Widowed"

class EducationLevel(enum.Enum):
    No_Matric = "Before Matric"
    High_School = "Passed Matric"
    College = "College"
    Bachelors = "Bachelor's Degree"
    Post_Grad = "Post Grad"

class AttendanceLevel(enum.Enum):
    Weekly = "Weekly"
    Bi_weekly = "Bi_weekly"
    Monthly = "Monthly"
    Rarely = "Rarely"

class Involvement(enum.Enum):
    Congregant = "Congregant"
    Server = "Server"
    Officer = "Officer"

class Yes_No(enum.Enum):
    Yes = "Yes"
    No = "No"

##################################################################

""" Set the tables"""
class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    event_date = Column(Date, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    location = Column(String(100), nullable=False)
    description = Column(Text)

class Member(Base):  # revise what can/cannot be nullable
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(String(20))
    gender = Column(Enum(Gender))
    phone_number = Column(String(15))
    email = Column(String(100), unique=True)
    address = Column(String(255))
    join_date = Column(String(20))
    membership_status = Column(Enum(MembershipStatus))

    # Relationships
    demographics = relationship("Demographics", back_populates="member")
    volunteer_opportunities = relationship("MemberVolunteering", back_populates="member")

class Demographics(Base):
    __tablename__ = 'demographics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    marital_status = Column(Enum(Marital_Status))
    children = Column(Integer, nullable=False)
    family_at_home = Column(Integer, nullable=False)
    #family_at_church = Column()   must revisit
    occupation = Column(String(90))  # leave blank if not employed
    education_level = Column(Enum(EducationLevel))
    attendance = Column(Enum(AttendanceLevel))
    involvement = Column(Enum(Involvement))
    disabilities = Column(Enum(Yes_No))

    # Relationships
    member = relationship("Member", back_populates="demographics")

class VolunteerOpportunity(Base):
    __tablename__ = 'volunteer_opportunities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    date_posted = Column(String(20), nullable=False)
    location = Column(String(100))

    # Relationships
    members = relationship("MemberVolunteering", back_populates="volunteer_opportunity")

class MemberVolunteering(Base):
    __tablename__ = 'member_volunteering'
    member_id = Column(Integer, ForeignKey('members.id'), primary_key=True)
    opportunity_id = Column(Integer, ForeignKey('volunteer_opportunities.id'), primary_key=True)
    date_volunteered = Column(String(20), nullable=False)

    # Relationships
    member = relationship("Member", back_populates="volunteer_opportunities")
    volunteer_opportunity = relationship("VolunteerOpportunity", back_populates="members")

# Create all tables
Base.metadata.create_all(engine)


""" Queries """
def get_all_events():  # no parms because its '.all()'
    try:
        result = session.query(Event).all()
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve events: {e}")  # exception to be handled by the caller

def get_event_by_name(ename):
    try:
        found = session.query(Event).filter_by(name=ename).first()
        if found:
            return found
        else:
            raise RuntimeError(f"event with name '{ename}' not found")
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve event with name '{ename}': {e}")  # exception to be handled by the caller

def get_event_by_date(date):
    try:
        found = session.query(Event).filter_by(event_date=date).first()
        if found:
            return found
        else:
            raise RuntimeError(f"event with date '{date}' not found")
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve event with date '{date}': {e}")  # exception to be handled by the caller

def get_all_members():  # no parms because its '.all()'
    try:
        result = session.query(Member).all()
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve members: {e}")  # exception to be handled by the caller

def get_member_by_email(email):
    try:
        result = session.query(Member).filter_by(email=email).first()
        return result
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve member with email '{email}': {e}")  # exception to be handled by the caller

def get_member_by_names(fname, lname ):
    try:
        result = session.query(Member).filter_by(first_name=fname, last_name=lname).first()
        return result
    except Exception as e:
        print(f"An error occurred: {e}")                                
        raise RuntimeError(f"Failed to retrieve member with names '{fname, lname}': {e}")  # exception to be handled by the caller

def married_members():
    try:
        married_members_query = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.marital_status == 'Married').all()
        result = [(member.id, member.first_name, member.last_name, member.join_date)  # a list of tuples (id, name, surname)
                for demo, member in married_members_query]    
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred while querying married members: {e}")
        raise RuntimeError(f"Failed to retrieve married members: {e}")

def children_query():
    try:
        c_query = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.children >= 1).all()  # greater or equal to 1
        result = [(member.id, member.first_name, member.last_name, demo.children)  # Create a list of tuples (id, name, surname)
                for demo, member in c_query]  # demo refers to results from Demographics table, unused in this case  
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred while querying members with children: {e}")
        raise RuntimeError(f"Failed to retrieve members with children: {e}")

def uneducated_members():
    try: 
        uneducated_membs = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.education_level == 'Before Matric').all()
        result = [(member.id, member.first_name, member.last_name, member.phone_number)  # Create a list of tuples (id, name, surname)
                for demo, member in uneducated_membs]    
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred while querying uneducated members: {e}")
        raise RuntimeError(f"Failed to retrieve uneducated members: {e}")

def educated_members():
    try: 
        educated_membs = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.education_level != 'Before Matric').all()
        result = [(member.id, member.first_name, member.last_name, member.phone_number)  # Create a list of tuples (id, name, surname)
                for demo, member in educated_membs]    
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred while querying educated members: {e}")
        raise RuntimeError(f"Failed to retrieve educated members: {e}")
    
def disabled_members():
    try:
        members_with_disabilities = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.disabilities == 'Yes').all()
        result = [(member.id, member.first_name, member.last_name, member.phone_number)  # Create a list of tuples (id, name, surname and phone number)
                for demo, member in members_with_disabilities]    
        count = len(result)
        return result, count
    except Exception as e:
        print(f"An error occurred while querying disabled members: {e}")
        raise RuntimeError(f"Failed to retrieve disabled members: {e}")

def office_bearers():
    try:
        servers = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.involvement == 'Server').all()
        result = [(member.id, member.first_name, member.last_name, member.phone_number, demo.involvement)  # Create a list of tuples (id, name, surname, phone number and office)
                for demo, member in servers] 
        officers = session.query(Demographics, Member).\
            join(Member, Demographics.member_id == Member.id).\
            filter(Demographics.involvement == 'Officer').all()
        result2 = [(member.id, member.first_name, member.last_name, member.phone_number, demo.involvement)  # Create a list of tuples (id, name, surname, phone number and office)
                for demo, member in officers] 
        count = len(result)
        count2 = len(result2)
        return result, result2, count, count2
    except Exception as e:
        print(f"An error occurred while querying serving members: {e}")
        raise RuntimeError(f"Failed to retrieve serving members: {e}")



# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Example: Adding a new member
#new_member = Member(
#    first_name="John",
#    last_name="Doe",
#    date_of_birth="1980-01-01",
#    gender=Gender.Male,
#    phone_number="+27 78 120 5705",
#    email="john.doe@example.com",
#    address="123 Alf Street",
#    join_date="2024-01-01",
#    membership_status=MembershipStatus.Active
#)

# Add and commit the new member
#session.add(new_member)
#session.commit()

print("Database is ready.")
