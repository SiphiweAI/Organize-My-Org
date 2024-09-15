import sys
import datetime
import logging
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Event, get_all_events, get_event_by_name, get_event_by_date
from models import Member, Demographics, get_all_members, get_member_by_names, get_member_by_email
from models import married_members, children_query, uneducated_members, disabled_members, office_bearers
from daily_tasks import send_reminders  # Import the function for sending reminders
from sqlalchemy.exc import SQLAlchemyError


# Configure logging
logging.basicConfig(
    filename='church_management.log',  # Log file
    level=logging.ERROR,               # Log level (you can set to INFO or DEBUG for more verbosity)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database setup
DATABASE_URL = "sqlite:///church.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Church Management System')
        self.setGeometry(100, 100, 1200, 800)

   
        # Create QStackedWidget and set it as central widget
        self.stacked_widget = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize widgets for each screen
        self.main_widget = self.create_main_widget()
        self.events_widget = EventsOperations(self)
        self.member_operations_widget = MemberOperations(self)
        self.query_operations_widget = QueryOperations(self)
        
        # Add widgets to the stacked widget
        self.stacked_widget.addWidget(self.main_widget)
        self.stacked_widget.addWidget(self.events_widget)
        self.stacked_widget.addWidget(self.member_operations_widget)
        self.stacked_widget.addWidget(self.query_operations_widget)

    def create_main_widget(self):
        # Main widget with buttons for navigation
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.events_button = QtWidgets.QPushButton('Events', self)
        self.events_button.clicked.connect(self.switch_to_events_operations)
        layout.addWidget(self.events_button, alignment=QtCore.Qt.AlignCenter)
        
        self.member_opp_button = QtWidgets.QPushButton('Member Operations', self)
        self.member_opp_button.clicked.connect(self.switch_to_member_operations)
        layout.addWidget(self.member_opp_button, alignment=QtCore.Qt.AlignCenter)

        self.query_button = QtWidgets.QPushButton('Query Members', self)
        self.query_button.clicked.connect(self.switch_to_queries)
        layout.addWidget(self.query_button, alignment=QtCore.Qt.AlignCenter)

        self.send_reminders_button = QtWidgets.QPushButton('Send Reminders', self)
        self.send_reminders_button.clicked.connect(self.send_reminders)
        layout.addWidget(self.send_reminders_button, alignment=QtCore.Qt.AlignCenter)
        
        return widget

    def switch_to_events_operations(self):
        self.stacked_widget.setCurrentWidget(self.events_widget)
    
    def switch_to_member_operations(self):
        self.stacked_widget.setCurrentWidget(self.member_operations_widget)

    def switch_to_queries(self):
        self.stacked_widget.setCurrentWidget(self.query_operations_widget)

    def send_reminders(self):
        try:
            send_reminders()
            QMessageBox.information(self, 'Success', 'Reminders have been sent.')
        except Exception as e:
            logging.error(f'Failed to send reminders: {e}', exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to send reminders: {e}')

    def go_back(self):
        self.stacked_widget.setCurrentWidget(self.main_widget)


class EventsOperations(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        

        ### search results are displayed here  ###
        # no label
        # text areas to display responses
        self.event_count_label = QtWidgets.QLabel('Number of events: ', self)
        self.event_count_label.setStyleSheet("font-size: 16px;")                              # no need to make it stand out
        self.event_count_label.setStyleSheet("background-color: white;")                # Set background to white NOT WORKING, ADJUST .qss file
        self.layout.addWidget(self.event_count_label, alignment=QtCore.Qt.AlignCenter)
        
        self.event_details_text_edit = QtWidgets.QTextEdit(self)
        self.event_details_text_edit.setReadOnly(True)
        self.event_details_text_edit.setStyleSheet("background-color: white;")                # Set background to white NOT WORKING, ADJUST .qss file
        self.event_details_text_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout.addWidget(self.event_details_text_edit, alignment=QtCore.Qt.AlignCenter)

        ### event search operations ###
        # label 1
        self.first_section_label = QtWidgets.QLabel('Event Search', self)
        self.first_section_label.setStyleSheet("font-weight: bold; font-size: 16px;")           # Make it stand out
        self.first_section_label.setAlignment(QtCore.Qt.AlignCenter)                            # Center the text
        self.layout.addWidget(self.first_section_label, alignment=QtCore.Qt.AlignCenter)

        # buttons
        button_layout = QtWidgets.QHBoxLayout()                                                 # 

        # searches
        self.show_all_e_button = QtWidgets.QPushButton('Show All Events', self)
        self.show_all_e_button.setMinimumWidth(150)  # Ensure the button is wide enough
        self.show_all_e_button.clicked.connect(self.show_all_events)
        button_layout.addWidget(self.show_all_e_button)

        self.search_e_by_name_button = QtWidgets.QPushButton('Search Events By Name', self)
        self.search_e_by_name_button.setMinimumWidth(150)  # Ensure the button is wide enough
        self.search_e_by_name_button.clicked.connect(self.search_e_by_name)
        button_layout.addWidget(self.search_e_by_name_button)

        self.search_e_by_date_button = QtWidgets.QPushButton('Search Events By Date', self)
        self.search_e_by_date_button.setMinimumWidth(150)                                        # Ensure the button is wide enough
        self.search_e_by_date_button.clicked.connect(self.search_e_by_date)
        button_layout.addWidget(self.search_e_by_date_button)

        self.layout.addLayout(button_layout)          

        ## Event CRUD Operation ##
        # label2
        self.sec_section_label = QtWidgets.QLabel('Add/Delete/Edit Events', self)
        self.sec_section_label.setStyleSheet("font-weight: bold; font-size: 16px;")           # Make it stand out
        self.sec_section_label.setAlignment(QtCore.Qt.AlignCenter)                            # Center the text
        self.layout.addWidget(self.sec_section_label, alignment=QtCore.Qt.AlignCenter)

        # buttons
        button_layout2 = QtWidgets.QHBoxLayout()  

        # one-clicks
        self.add_e_button = QtWidgets.QPushButton('Add an Event', self)
        self.add_e_button.setMinimumWidth(150)                                                   # Ensure the button is wide enough
        self.add_e_button.clicked.connect(self.add_event)
        button_layout2.addWidget(self.add_e_button)

        self.remove_e_button = QtWidgets.QPushButton('Remove an Event', self)
        self.remove_e_button.setMinimumWidth(150)                                        # Ensure the button is wide enough
        self.remove_e_button.clicked.connect(self.remove_event)
        button_layout2.addWidget(self.remove_e_button)

        self.edit_e_button = QtWidgets.QPushButton('Edit an Event', self)
        self.edit_e_button.setMinimumWidth(150)                                             # Ensure the button is wide enough
        self.edit_e_button.clicked.connect(self.edit_event)
        button_layout2.addWidget(self.edit_e_button)


        self.layout.addLayout(button_layout2)          


        self.back_button = QtWidgets.QPushButton('Back', self)
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(self.layout)

    # functions

    def show_all_events(self):
        try:
            events, count = get_all_events()                                                  # the function returns two things: member list and count
            self.event_count_label.setText(f"Total number of events: {count}")
            event_details = "Name\tDate\tDescription\n"                                  # member details string with headings
            event_details += "-" * 80 + "\n"                                                   # a separator line

            for event in events:
                event_details += (
                f"{event.name}\t"
                f"{event.event_date}\t"
                f"{event.description}\n"                                           # adds spacing between members
                )
            self.event_details_text_edit.setPlainText(event_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def search_e_by_name(self):
        try:
            name, _ = QtWidgets.QInputDialog.getText(self, 'Search for Event', 'Event name:')
            event = get_event_by_name(name)                                                  # returns the object instance found on the db
            if event:
                details = (
                    f"Name: {event.name}\n"
                    f"Date: {event.event_date}\n"
                    f"Starting Time: {event.start_time}\n"
                    f"Finishing Time: {event.end_time}\n"
                    f"Location: {event.location}\n"
                    f"Description: {event.description}"
                )
                self.event_details_text_edit.setPlainText(details)                                     # display event details on the text box
            else:
                self.event_details_text_edit.setPlainText("Event not found")
        except Exception as e:
            self.event_details_text_edit.setPlainText(f"An error occurred: {e}")

    def search_e_by_date(self):
        try:
            event_date_str, _ = QtWidgets.QInputDialog.getText(self, 'Event Search', 'Date of Event (YYYY-MM-DD):')
            event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()            
            event = get_event_by_date(event_date)                                                  # returns the object instance found on the db
            if event:
                details = (
                    f"Name: {event.name}\n"
                    f"Date: {event.event_date}\n"
                    f"Starting Time: {event.start_time}\n"
                    f"Finishing Time: {event.end_time}\n"
                    f"Location: {event.location}\n"
                    f"Description: {event.description}"
                )
                self.event_details_text_edit.setPlainText(details)                                     # display event details on the text box
            else:
                self.event_details_text_edit.setPlainText("Event not found")
        except Exception as e:
            self.event_details_text_edit.setPlainText(f"An error occurred: {e}")

    def add_event(self):
            while True:                                                                 # Loop to allow retrying if needed
                try:
                    name, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'First Name:')
                    event_date_str, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'Date of Event (YYYY-MM-DD):')
                    event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                    start_time, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'Starting Time:')
                    end_time, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'Finishing Time:')
                    location, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'Location:')
                    description, _ = QtWidgets.QInputDialog.getText(self, 'Add Event', 'Description:')

                    event = Event(
                        name=name,
                        event_date=event_date,
                        start_time=start_time,
                        end_time=end_time,
                        location=location,
                        description=description
                        )
                
                # avoid adding duplicates
                    existing_event = session.query(Event).filter_by(name=name, event_date=event_date).first()
                    if existing_event:
                        response = QMessageBox.warning(self, 'Error', 'An event with this name and date already exists. Would you like to try again?', QMessageBox.Yes | QMessageBox.No)
                        if response == QMessageBox.No:
                            return
                        continue

                    session.add(event)
                    session.commit()
                    QMessageBox.information(self, 'Success', 'Member added successfully!')
        
                except Exception as e:
                    session.rollback()
                    logging.error(f'Failed to add member: {e}', exc_info=True)
                    QMessageBox.warning(self, 'Error', f'Failed to add member: {e}')

    def remove_event(self):
        try:
            name, _ = QtWidgets.QInputDialog.getText(self, 'Remove Event', 'Event Name:')
            doe_str, _ = QtWidgets.QInputDialog.getText(self, 'Remove Event', 'Date of Event (YYYY-MM-DD):')
            event_date = datetime.datetime.strptime(doe_str, '%Y-%m-%d').date()

            event = session.query(Event).filter_by(
                name=name,
                event_date=event_date
            ).first()

            if event:
                # Show event details for confirmation
                event_info = (
                    f"Name: {event.name}\n"
                    f"Date of Event: {event.event_date}\n"
                    f"Description: {event.description}"
                )
                reply = QMessageBox.question(self, 'Confirm Removal', f"Is this the event you want to remove?\n\n{event_info}",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Remove the member
                    session.delete(event)
                    session.commit()
                    QMessageBox.information(self, 'Success', 'Event removed successfully!')
                else:
                    QMessageBox.information(self, 'Cancelled', 'Process has been cancelled.')
            else:
                QMessageBox.information(self, 'Not Found', 'Event not found.')
        except Exception as e:
            session.rollback()
            logging.error(f'Failed to remove event: {e}', exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to remove event: {e}')

    def edit_event(self):
        try:
            name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'Name:')
            doe_str, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'Date of Event (YYYY-MM-DD):')
            event_date = datetime.datetime.strptime(doe_str, '%Y-%m-%d').date()

            event = session.query(Event).filter_by(
                name=name,
                event_date=event_date
            ).first()

            if event:
                # Show event details for confirmation
                event_info = (
                    f"Name: {event.name}\n"
                    f"Date of Event: {event.event_date}\n"
                    f"Event Start Time: {event.start_time}\n"
                    f"Event Finishing Time: {event.end_time}\n"
                    f"Event Location: {event.location}\n"
                    f"Event Description: {event.description}"
                )
                
                reply = QMessageBox.question(self, 'Confirm Edit', f"Is this is the event you want to edit?\n\n{event_info}",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Get new details
                    new_name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Name (leave blank if unchanged):', text=event.name)
                    new_doe_str, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Date of Event (leave blank if unchanged):', text=event.event_date.strftime('%Y-%m-%d'))
                    new_start_time, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Starting Time (leave blank if unchanged):', text=event.start_time)
                    new_end_time, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Finishing Time (leave blank if unchanged):', text=event.end_time)
                    new_location, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Venue (leave blank if unchanged):', text=event.location)
                    new_description, _ = QtWidgets.QInputDialog.getText(self, 'Edit Event', 'New Description (leave blank if unchanged):', text=event.description)

                    # Update event details only if new values are provided
                    if new_name:
                        event.name = new_name
                    if new_doe_str:
                        event.event_date = datetime.datetime.strptime(new_doe_str, '%Y-%m-%d').date()
                    if new_start_time:
                        event.start_time = new_start_time
                    if new_end_time:
                        event.end_time = new_end_time
                    if new_location:
                        event.location = new_location
                    if new_description:
                        event.description = new_description

                    session.commit()
                    QMessageBox.information(self, 'Success', 'Event details updated successfully!')
                else:
                    QMessageBox.information(self, 'Cancelled', 'Event editing has been cancelled.')
            else:
                QMessageBox.information(self, 'Not Found', 'Event not found.')
        except Exception as e:
            session.rollback()
            logging.error(f'Failed to edit event: {e}', exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to update event details: {e}')

    def go_back(self):
        session.rollback()
        self.main_window.go_back()


class MemberOperations(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        self.add_member_button = QtWidgets.QPushButton('Add Member', self)
        self.add_member_button.clicked.connect(self.add_member)
        layout.addWidget(self.add_member_button, alignment=QtCore.Qt.AlignCenter)

        self.remove_member_button = QtWidgets.QPushButton('Remove Member', self)
        self.remove_member_button.clicked.connect(self.remove_member)
        layout.addWidget(self.remove_member_button, alignment=QtCore.Qt.AlignCenter)

        self.edit_member_button = QtWidgets.QPushButton('Edit Member', self)
        self.edit_member_button.clicked.connect(self.edit_member)
        layout.addWidget(self.edit_member_button, alignment=QtCore.Qt.AlignCenter)

        self.back_button = QtWidgets.QPushButton('Back', self)
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button, alignment=QtCore.Qt.AlignCenter)


        self.setLayout(layout)

    def get_valid_integer(self, prompt):
                while True:
                    text, ok = QtWidgets.QInputDialog.getText(self, 'Member Details', prompt)
                    if ok:                                                        # Check if user pressed OK
                        try:
                            value = int(text)                                     # convert input into int
                            return value
                        except ValueError:
                            QtWidgets.QMessageBox.warning(self, 'Input Error', 'Invalid input. Please enter a valid number.')
                    else:
                        return None                # If the dialog is canceled, return None or handle accordingly

    def add_member(self):                                   # adjust read_members_from_txt and add_members_to_db to fit how the Google Form is expected
        while True:                                                                 # Loop to allow retrying if needed
            try:
                kind_of_adding, _ =  QtWidgets.QInputDialog.getItem(self, 'Adding Members', 'How would you like to add members', ['Upload a txt File', 'Input Details'])
                if kind_of_adding == 'Upload a txt File':
                    try:
                        def read_members_from_txt(file_path):                       # adjust len: depends on the txt doc
                            members = []
                            try:
                                with open(file_path, 'r') as file:
                                    lines = file.readlines()
                                    # Skip the header
                                    for line in lines[1:]:
                                        parts = line.strip().split('|')                                      # choose the appropriate limmiter ',' or '|'
                                        if len(parts) == 11:                                                 # number of columns
                                            first_name, last_name, email, phone_number, marital_status, children, family_at_home, occupation, education_level, involvement, disabilities = parts
                                            try:
                                                members.append((first_name, last_name, email, phone_number, marital_status, children, family_at_home, occupation, education_level, involvement, disabilities))  # Allocate specific columns to members table
                                            except ValueError:
                                                # Handle conversion errors (e.g., age is not an integer)
                                                QMessageBox.information(f"Skipping invalid line: {line.strip()}")
                            except IOError as e:
                                QMessageBox.information(f"Error reading file: {e}")
                            return members                 # allocate specific columns to members table

                        def add_members_to_db(members):                             # adjust new_member and new_demographics columns: depends on members.append in read_members_from_txt  
                            try:
                                for first_name, last_name, email, phone_number, marital_status, children, family_at_home, occupation, education_level, involvement, disabilities in members:
                                    with session.begin():                                           # Begin a transaction
                                        new_member = Member(first_name=first_name, last_name=last_name, email=email, phone_number=phone_number)     
                                        session.add(new_member)
                                        # Commit here to get the new_member.id
                                        # This ensures that new_member.id is available for the next step
                                        session.flush()
                                        
                                        new_demographics = Demographics(member_id=new_member.id, marital_status=marital_status, children=children, family_at_home=family_at_home, occupation=occupation, education_level=education_level, involvement=involvement, disabilities=disabilities)
                                        session.add(new_demographics)
                                        
                                        # Commit the transaction, making sure both member and demographics are saved
                                        session.commit()
                            except SQLAlchemyError as e:
                                # Handle database errors
                                session.rollback()  # Rollback in case of error
                                print(f"Database error: {e}")
                            except Exception as e:
                                # Catch all other exceptions
                                session.rollback()  # Rollback in case of error
                                print(f"Unexpected error: {e}")

                        def load_file(self):
                            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt)")
                            if file_path:
                                try:
                                    members = read_members_from_txt(file_path)
                                    if not members:
                                        QMessageBox.information('No valid data found in the file.')
                                        return
                                    add_members_to_db(members)
                                    QMessageBox.information('Members imported successfully.')
                                except Exception as e:
                                    QMessageBox.information(self,'An error occurred during import.')
                                    QMessageBox.information(f"Error during import: {e}")
                        
                        load_file()

                    except Exception as e:
                        QMessageBox.information(self,'An error occurred during adding file.')

                if kind_of_adding == 'Input Details':
                    try:
                        first_name, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'First Name:')
                        last_name, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Last Name:')
                        dob_str, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Date of Birth (YYYY-MM-DD):')
                        date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
                        gender, _ = QtWidgets.QInputDialog.getItem(self, 'Add Member', 'Gender:', ['Male', 'Female', 'Other'])
                        phone_number, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Phone Number:')
                        email, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Email:')
                        address, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Address:')
                        join_date_str, _ = QtWidgets.QInputDialog.getText(self, 'Add Member', 'Join Date (YYYY-MM-DD):')
                        join_date = datetime.datetime.strptime(join_date_str, '%Y-%m-%d').date()
                        membership_status, _ = QtWidgets.QInputDialog.getItem(self, 'Add Member', 'Membership Status:', ['Active', 'Inactive'])
                        
                        member = Member(
                            first_name=first_name,
                            last_name=last_name,
                            date_of_birth=date_of_birth,
                            gender=gender,
                            phone_number=phone_number,
                            email=email,
                            address=address,
                            join_date=join_date,
                            membership_status=membership_status
                        )
                    
                    # avoid adding duplicates
                        existing_member = session.query(Member).filter_by(first_name=first_name, last_name=last_name, date_of_birth=date_of_birth).first()
                        if existing_member:
                            response = QMessageBox.warning(self, 'Error', 'A member with this name and date of birth already exists. Would you like to try again?', QMessageBox.Yes | QMessageBox.No)
                            if response == QMessageBox.No:
                                return
                            continue

                        existing_email = session.query(Member).filter_by(email=email).first()
                        if existing_email:
                            response = QMessageBox.warning(self, 'Error', 'A member with this email already exists. Would you like to try again?', QMessageBox.Yes | QMessageBox.No)
                            if response == QMessageBox.No:
                                return
                            continue

                        marital_status, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Marital Status:', ['Married', 'Never Married', 'Divorced', 'Widowed'])
                        children = self.get_valid_integer('How many children do you have:')                             # calls the get_valid_integer func passing the phrase
                        family_at_home = self.get_valid_integer('Number of people at home:')
                        occupation, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Occupation:')
                        education_level, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Education Level:', ['Before Matric', 'Passed Matric', 'College', 'Bachelors Degree', 'Post Grad'])
                        attendance, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Attendance:', ['Bi-Weekly', 'Weekly', 'Monthly', 'Rarely'])
                        involvement, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Involvement:', ['Congregant', 'Server', 'Officer'])
                        disabilities, _ = QtWidgets.QInputDialog.getItem(self, 'Member Details', 'Disabilities:', ['Yes', 'No'])

                        session.add(member)
                        session.commit()                            # commit here so we can have member ID to link in demogs

                        demogs = Demographics(
                            marital_status=marital_status,
                            children=children,
                            family_at_home=family_at_home,
                            occupation=occupation,
                            education_level=education_level,
                            attendance=attendance,
                            involvement=involvement,
                            disabilities=disabilities,
                            member_id=member.id                     # Link demographics to the newly created member
                        )
            
                        session.add(demogs)
                        session.commit()
                        QMessageBox.information(self, 'Success', 'Member added successfully!')
            
                    except Exception as e:
                        session.rollback()
                        logging.error(f'Failed to add member: {e}', exc_info=True)
                        QMessageBox.warning(self, 'Error', f'Failed to add member: {e}')

            except Exception as e:
                QMessageBox.information(self,'An error occurred during adding member(s).')

    def remove_member(self):
        try:
            first_name, _ = QtWidgets.QInputDialog.getText(self, 'Remove Member', 'First Name:')
            last_name, _ = QtWidgets.QInputDialog.getText(self, 'Remove Member', 'Last Name:')
            dob_str, _ = QtWidgets.QInputDialog.getText(self, 'Remove Member', 'Date of Birth (YYYY-MM-DD):')
            date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()

            member = session.query(Member).filter_by(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth
            ).first()

            if member:
                # Show member details for confirmation
                member_info = (
                    f"Name: {member.first_name} {member.last_name}\n"
                    f"Date of Birth: {member.date_of_birth}\n"
                    f"Phone Number: {member.phone_number}\n"
                    f"Email: {member.email}\n"
                    f"Address: {member.address}\n"
                    f"Membership Status: {member.membership_status}"
                )
                reply = QMessageBox.question(self, 'Confirm Removal', f"Is this the member you want to remove?\n\n{member_info}",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Remove the member
                    session.delete(member)
                    session.commit()
                    QMessageBox.information(self, 'Success', 'Member removed successfully!')
                else:
                    QMessageBox.information(self, 'Cancelled', 'Process has been cancelled.')
            else:
                QMessageBox.information(self, 'Not Found', 'Member not found.')
        except Exception as e:
            session.rollback()
            logging.error(f'Failed to remove member: {e}', exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to remove member: {e}')

    def edit_member(self):
        try:
            first_name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'First Name:')
            last_name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'Last Name:')
            dob_str, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'Date of Birth (YYYY-MM-DD):')
            date_of_birth = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()

            member = session.query(Member).filter_by(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth
            ).first()

            if member:
                # Show member details for confirmation
                member_info = (
                    f"Name: {member.first_name} {member.last_name}\n"
                    f"Date of Birth: {member.date_of_birth}\n"
                    f"Phone Number: {member.phone_number}\n"
                    f"Email: {member.email}\n"
                    f"Address: {member.address}\n"
                    f"Membership Status: {member.membership_status}"
                )
                
                reply = QMessageBox.question(self, 'Confirm Edit', f"Is this the member you want to edit?\n\n{member_info}",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    # Get new details
                    new_first_name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New First Name (leave blank if unchanged):', text=member.first_name)
                    new_last_name, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New Last Name (leave blank if unchanged):', text=member.last_name)
                    new_dob_str, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New Date of Birth (leave blank if unchanged):', text=member.date_of_birth.strftime('%Y-%m-%d'))
                    new_phone_number, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New Phone Number (leave blank if unchanged):', text=member.phone_number)
                    new_email, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New Email (leave blank if unchanged):', text=member.email)
                    new_address, _ = QtWidgets.QInputDialog.getText(self, 'Edit Member', 'New Address (leave blank if unchanged):', text=member.address)
                    new_status, _ = QtWidgets.QInputDialog.getItem(self, 'Edit Member', 'New Membership Status (leave unchanged if current):', ['Active', 'Inactive'], current=member.membership_status)

                    # Update member details only if new values are provided
                    if new_first_name:
                        member.first_name = new_first_name
                    if new_last_name:
                        member.last_name = new_last_name
                    if new_dob_str:
                        member.date_of_birth = datetime.datetime.strptime(new_dob_str, '%Y-%m-%d').date()
                    if new_phone_number:
                        member.phone_number = new_phone_number
                    if new_email:
                        member.email = new_email
                    if new_address:
                        member.address = new_address
                    if new_status:
                        member.membership_status = new_status

                    session.commit()
                    QMessageBox.information(self, 'Success', 'Member details updated successfully!')
                else:
                    QMessageBox.information(self, 'Cancelled', 'Member editing has been cancelled.')
            else:
                QMessageBox.information(self, 'Not Found', 'Member not found.')
        except Exception as e:
            session.rollback()
            logging.error(f'Failed to edit member: {e}', exc_info=True)
            QMessageBox.warning(self, 'Error', f'Failed to update member details: {e}')

    def go_back(self):
        session.rollback()
        self.main_window.go_back()


class QueryOperations(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()
    
    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout(self)


        ### search results are displayed here  ###
        # no label
        # text areas to display responses
        self.member_count_label = QtWidgets.QLabel('Number of members: ', self)
        self.member_count_label.setStyleSheet("font-size: 16px;")                              # no need to make it stand out
        self.member_count_label.setStyleSheet("background-color: white;")                # Set background to white NOT WORKING, ADJUST .qss file
        self.layout.addWidget(self.member_count_label, alignment=QtCore.Qt.AlignCenter)
        
        self.member_details_text_edit = QtWidgets.QTextEdit(self)
        self.member_details_text_edit.setReadOnly(True)
        self.member_details_text_edit.setStyleSheet("background-color: white;")                # Set background to white NOT WORKING, ADJUST .qss file
        self.member_details_text_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout.addWidget(self.member_details_text_edit, alignment=QtCore.Qt.AlignCenter)

        ### member search operations ###
        # label 1
        self.first_section_label = QtWidgets.QLabel('Member Search', self)
        self.first_section_label.setStyleSheet("font-weight: bold; font-size: 16px;")           # Make it stand out
        self.first_section_label.setAlignment(QtCore.Qt.AlignCenter)                            # Center the text
        self.layout.addWidget(self.first_section_label, alignment=QtCore.Qt.AlignCenter)

        # buttons
        button_layout = QtWidgets.QHBoxLayout()                                                 # 

        # searches
        self.show_all_button = QtWidgets.QPushButton('Show All Members', self)
        self.show_all_button.setMinimumWidth(150)  # Ensure the button is wide enough
        self.show_all_button.clicked.connect(self.show_all_members)
        button_layout.addWidget(self.show_all_button)

        self.search_by_name_button = QtWidgets.QPushButton('Search By Name', self)
        self.search_by_name_button.setMinimumWidth(150)  # Ensure the button is wide enough
        self.search_by_name_button.clicked.connect(self.search_by_full_name)
        button_layout.addWidget(self.search_by_name_button)

        self.search_by_email_button = QtWidgets.QPushButton('Search By Email', self)
        self.search_by_email_button.setMinimumWidth(150)                                        # Ensure the button is wide enough
        self.search_by_email_button.clicked.connect(self.search_by_email)
        button_layout.addWidget(self.search_by_email_button)

        self.layout.addLayout(button_layout)          

        # label2
        self.sec_section_label = QtWidgets.QLabel('Stats Section', self)
        self.sec_section_label.setStyleSheet("font-weight: bold; font-size: 16px;")           # Make it stand out
        self.sec_section_label.setAlignment(QtCore.Qt.AlignCenter)                            # Center the text
        self.layout.addWidget(self.sec_section_label, alignment=QtCore.Qt.AlignCenter)

        # buttons
        button_layout2 = QtWidgets.QHBoxLayout()  

        # one-clicks
        self.married_button = QtWidgets.QPushButton('Married Members', self)
        self.married_button.setMinimumWidth(150)                                                   # Ensure the button is wide enough
        self.married_button.clicked.connect(self.member_married)
        button_layout2.addWidget(self.married_button)

        self.search_m_with_kids_button = QtWidgets.QPushButton('Members With Children', self)
        self.search_m_with_kids_button.setMinimumWidth(150)                                        # Ensure the button is wide enough
        self.search_m_with_kids_button.clicked.connect(self.member_with_children)
        button_layout2.addWidget(self.search_m_with_kids_button)

        self.search_uneduc_button = QtWidgets.QPushButton('Uneducated Members', self)
        self.search_uneduc_button.setMinimumWidth(150)                                             # Ensure the button is wide enough
        self.search_uneduc_button.clicked.connect(self.uneduc_members)
        button_layout2.addWidget(self.search_uneduc_button)

        self.search_disabled_m_button = QtWidgets.QPushButton('Disabled Members', self)
        self.search_disabled_m_button.setMinimumWidth(150)                                           # Ensure the button is wide enough
        self.search_disabled_m_button.clicked.connect(self.members_disabled)
        button_layout2.addWidget(self.search_disabled_m_button)

        self.search_officers_button = QtWidgets.QPushButton('Servers/Annointed Members', self)
        self.search_officers_button.setMinimumWidth(150)                                           # Ensure the button is wide enough
        self.search_officers_button.clicked.connect(self.officers_servers)
        button_layout2.addWidget(self.search_officers_button)

        self.layout.addLayout(button_layout2)          

        self.back_button = QtWidgets.QPushButton('Back', self)          
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(self.layout)

        
    def go_back(self):
        session.rollback()
        self.member_count_label.setText('Number of members: ')                                  # reverts
        self.member_details_text_edit.clear()                                                   # Clear the text edit area
        self.main_window.go_back()

    # searches
    def show_all_members(self):
        try:
            members, count = get_all_members()                                                  # the function returns two things: member list and count
            self.member_count_label.setText(f"Total number of members: {count}")
            member_details = "Name\tPhone Number\tJoin Date\n"                                  # member details string with headings
            member_details += "-" * 80 + "\n"                                                   # a separator line

            for member in members:
                member_details += (
                f"{member.id}\t"
                f"{member.first_name} {member.last_name}\t"
                f"{member.join_date}\n"                                           # adds spacing between members
                )
            self.member_details_text_edit.setPlainText(member_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def search_by_full_name (self):
        try:
            fname, _ = QtWidgets.QInputDialog.getText(self, 'Search for Member', 'First Name:')
            lname, _ = QtWidgets.QInputDialog.getText(self, 'Search for Member', 'Last Name:')
            member = get_member_by_names(fname, lname)                                                  # returns the object instance found on the db
            if member:
                details = (
                    f"Name: {member.first_name} {member.last_name}\n"
                    f"Email: {member.email}\n"
                    f"Phone Number: {member.phone_number}\n"
                    f"Address: {member.address}\n"
                    f"Join Date: {member.join_date}"
                )
                self.member_details_text_edit.setPlainText(details)                                     # display member details on the text box
            else:
                self.member_details_text_edit.setPlainText("Member not found")
        except Exception as e:
            self.member_details_text_edit.setPlainText(f"An error occurred: {e}")

    def search_by_email (self):
        try:
            email, _ = QtWidgets.QInputDialog.getText(self, 'Search for Member', 'Email:')
            member = get_member_by_email(email)                                                  # returns the object instance found on the db
            if member:
                details = (
                    f"Name: {member.first_name} {member.last_name}\n"
                    f"Email: {member.email}\n"
                    f"Phone Number: {member.phone_number}\n"
                    f"Address: {member.address}\n"
                    f"Join Date: {member.join_date}"
                )
                self.member_details_text_edit.setPlainText(details)                                     # display member details on the text box
            else:
                self.member_details_text_edit.setPlainText("Member not found")
        except Exception as e:
            self.member_details_text_edit.setPlainText(f"An error occurred: {e}")

    # queries
    def member_married(self):
        try:
            members, count = married_members()                                                  # the function returns two things: member list and count
            self.member_count_label.setText(f"Total number of members: {count}")
            member_details = "Member ID\tName\tJoin Date\n"                                     # member details string with headings
            member_details += "-" * 80 + "\n"                                                   # a separator line
            for member in members:
                member_details += (
                f"{member.id}\t"
                f"{member.first_name} {member.last_name}\t"
                f"{member.join_date}\n\n"                                                       # adds spacing between members
                )
            self.member_details_text_edit.setPlainText(member_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def member_with_children(self):
        try:
            members, count = children_query()                                                  # the function returns two things: member list and count
            self.member_count_label.setText(f"Total number of members: {count}")
            member_details = "Member ID\tName\tNumber of children\n"                                     # member details string with headings
            member_details += "-" * 80 + "\n"                                                   # a separator line
            for member in members:
                member_details += (
                    f"{member[0]}\t"                                                            # member.id
                    f"{member[1]} {member[2]}\t"                                                # member.first_name and member.last_name
                    f"{member[3]}\n\n"                                                          # member.children
            )
            self.member_details_text_edit.setPlainText(member_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def uneduc_members(self):
        try:
            members, count = uneducated_members()                                               # the function returns two things: member list and count
            self.member_count_label.setText(f"Number of uneducated members: {count}")
            member_details = "Member ID\tName\tPhone Number\n"                                     # member details string with headings
            member_details += "-" * 80 + "\n"                                                   # a separator line
            for member in members:
                member_details += (
                    f"{member[0]}\t"                                                            # member.id
                    f"{member[1]} {member[2]}\t"                                                # member.first_name and member.last_name
                    f"{member[3]}\n\n"                                                          # member.children
            )
            self.member_details_text_edit.setPlainText(member_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def members_disabled(self):
        try:
            members, count = disabled_members()                                               # the function returns two things: member list and count
            self.member_count_label.setText(f"Number of disabled members: {count}")
            member_details = "Member ID\tName\tPhone Number\n"                                     # member details string with headings
            member_details += "-" * 80 + "\n"                                                   # a separator line
            for member in members:
                member_details += (
                    f"{member[0]}\t"                                                            # member.id
                    f"{member[1]} {member[2]}\t"                                                # member.first_name and member.last_name
                    f"{member[3]}\n\n"                                                          # member.phone number
            )
            self.member_details_text_edit.setPlainText(member_details)                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))

    def officers_servers(self):
        try:
            servers, officers, count, count2 = office_bearers()                                               # the function returns four things: 2x member list and 2x count
            self.member_count_label.setText(f"Number of Servers: {count}\nNumber of Annointed Members: {count2}")
            server_details = "Member ID\tName\tPhone Number\tRole\n"                                     # member details string with headings
            officer_details = ""                                                                   # member details with no headings
            server_details += "-" * 80 + "\n"                                                   # a separator line
            officer_details += "-" * 80 + "\n"                                                   # a separator line
            for member in servers:
                server_details += (
                    f"{member[0]}\t"                                                            # member.id
                    f"{member[1]} {member[2]}\t"                                                # member.first_name and member.last_name
                    f"{member[3]}\t"                                                            # member.phone number
                    f"{member[4]}\n\n"                                                          # demo.involvement
            )
            for member in officers:
                officer_details += (
                    f"{member[0]}\t"                                                            # member.id
                    f"{member[1]} {member[2]}\t"                                                # member.first_name and member.last_name
                    f"{member[3]}\t"                                                            # member.phone number
                    f"{member[4]}\n\n"                                                          # demo.involvement
            )
            self.member_details_text_edit.setPlainText(f"{server_details}\n\n{officer_details}")                          # Update the text area with members' details
        except RuntimeError as e:
            QtWidgets.QMessageBox.critical(self, 'Error', str(e))















   # def query_members(self):
   #     try:
   #         query = session.query(Member).all()
   #         result = "\n".join([f"{member.first_name} {member.last_name} - {member.email}" for member in query])
   #         QMessageBox.information(self, 'Members List', result if result else 'No members found.')
   #     except Exception as e:
   #         logging.error(f'Failed to query members: {e}', exc_info=True)
   #         QMessageBox.warning(self, 'Error', f'Failed to query members: {e}')




""" styling using style sheets """
def apply_stylesheet(app):
    with open("stylesheet.qss", "r") as file:          
        qss = file.read()
        app.setStyleSheet(qss)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app)                           # Apply the stylesheet
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
