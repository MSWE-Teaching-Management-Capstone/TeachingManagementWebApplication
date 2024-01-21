import os
from flask import Flask, redirect
from dotenv import load_dotenv

from .views.auth import auth
from .views.faculty import faculty
from .views.logs import logs
from .views.settings import settings
from .views.course import courses
import click
from flask.cli import with_appcontext
from .models import Users, FacultyStatus, FacultyPointInfo, Courses, ScheduledTeaching, Exceptions, Rules, Logs, db

load_dotenv('.flaskenv')
load_dotenv('.env')


def init_rules():
    rules = [
        Rules(rule_name='Role-tenured research faculty', value=3.5),
        Rules(rule_name='Role-faculty up for tenure', value=3.5),
        Rules(rule_name='Role-assistant professor (1st year)', value=1),
        Rules(rule_name='Role-assistant professor (2nd+ year)', value=2.5),
        Rules(rule_name='Role-tenured POT', value=6.5),
        Rules(rule_name='Role-poT up for tenure', value=6.5),
        Rules(rule_name='Role-assistant POT (1st year)', value=5),
        Rules(rule_name='Role-assistant POT (2nd+ year)', value=5.5),
        Rules(rule_name='Category 0', value=1.5),
        Rules(rule_name='Category 1', value=1.25),
        Rules(rule_name='Category 2', value=1),
        Rules(rule_name='Category 3', value=0.75),
        Rules(rule_name='Category 4', value=0.25)
    ]

    db.session.bulk_save_objects(rules)
    db.session.commit()

def init_courses():
    courses = [
        Courses(course_title_id='CS143B', course_title='PROJECT IN OPERATING SYSTEM ORGANIZATION', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS45C', course_title='PROGRAMMING IN C/C++ AS A SECOND LANGUAGE', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS141', course_title='CONCEPTS IN PROGRAMMING LANGUAGES', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS143A', course_title='LANGUAGE PROCESSOR CONSTRUCTION', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS180A', course_title='SPECIAL TOPICS: PROJECT IN COMPUTER SCIENCE', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS180B', course_title='SPECIAL TOPICS: PROJECT IN COMPUTER SCIENCE', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS5', course_title='ENVIRONMENTAL ISSUES IN INFORMATION TECHNOLOGY', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS6B', course_title='BOOLEAN ALGEBRA & LOGIC', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS6D', course_title='DISCRETE MATHEMATICS FOR COMPUTER SCIENCE', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS32', course_title='PROGRAMMING WITH SOFTWARE LIBRARIES', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS32A', course_title='PYTHN PGMG LIBR/ACC', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS60', course_title='COMPUTER GAMES & SOCIETY', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS139W', course_title='CRITICAL WRITING ON INFORMATION TECHNOLOGY', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS103', course_title='ADVANCED PROGRAMMING & PROBLEM SOLVING WITH C++', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS111', course_title='DIGITAL IMAGE PROCESSING', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS112', course_title='COMPUTER GRAPHICS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS113', course_title='COMPUTER GAME DEVELOPMENT', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS114', course_title='PROJECTS IN ADVANCED 3D COMPUTER GRAPHICS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS115', course_title='COMPUTER SIMULATION', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS116', course_title='COMPUTATIONAL PHOTOGRAPHY & VISION', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS117', course_title='PROJECT IN COMPUTER VISION', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS118', course_title='INTRODUCTION TO VR', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS121', course_title='INFORMATION RETRIEVAL', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS122A', course_title='INTRODUCTION TO DATA MANAGEMENT', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS122B', course_title='PROJECT IN DATABASES & WEB APPLICATIONS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS122C', course_title='PRINCIPLES OF DATA MANAGEMENT', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS122D', course_title='BEYOND SQL DATA MANAGEMENT', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS125', course_title='NEXT GENERATION SEARCH SYSTEMS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS131', course_title='PARELLEL & DISTRIBUTED COMPUTING', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS132', course_title='COMPUTER NETWORKS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS133', course_title='ADVANCED COMPUTER NETWORKS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS134', course_title='COMPUTER & NETWORK SECURITY', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS137', course_title='INTERNET APPLICATIONS ENGINEERING', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS142A', course_title='COMPILERS & INTERPRETERS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS142B', course_title='PRINCICPLES OF OPERATING SYSTEMS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS145', course_title='EMBEDDED SOFTWARE', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS145L', course_title='EMBEDDED SOFTWARE LABORATORY', units=2, course_level='Undergrad'),
        Courses(course_title_id='CS146', course_title='PROGRAMMING IN MULTITASKING OPERATING SYSTEMS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS147', course_title='IOT SOFTWARE & SYSTEMS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS151', course_title='DIGITAL LOGIC DESIGN', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS152', course_title='COMPUTER SYSTEMS ARCHITECTURE', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS153', course_title='LOGIC DESIGN LABORATORY', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS154', course_title='COMPUTER DESIGN LABORATORY', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS161', course_title='DESIGN & ANALYSIS OF ALGORITHMS', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS162', course_title='FORMAL LANGUAGES & AUTOMATA', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS163', course_title='GRAPH ALGORITHMS', units=4, course_level='Undergrad', combine_with='CS265'),
        Courses(course_title_id='CS164', course_title='COMPUTATIONAL GEOMETRY & GEOMETRIC MODELING', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS165', course_title='PROJECT IN ALGORITHMS & DATA STRUCTURES', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS166', course_title='QUANTUM COMPUTATION & INFORMATION', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS167', course_title='INTRODUCTION TO APPLIED CRYPTOGRAPHY', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS169', course_title='INTRODUCTION TO OPTIMIZATION', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS171', course_title='INTRODUCTION TO ARTIFICIAL INTELLIGENCE', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS172B', course_title='NEURAL NETWORKS & DEEP LEARNING', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS172C', course_title='ARTIFICIAL INTELLIGENCE FRONTIERS: TECHNICAL, ETHICAL, AND SOCIETAL', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS175', course_title='PROJECT IN ARTIFICIAL INTELLIGENCE', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS177', course_title='APPLICATION OF PROBABILITY IN COMPUTER SCIENCE', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS178', course_title='MACHINE LEARNING & DATA-MINING', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS179', course_title='ALGORITHMS FOR PROBABILISTIC & DETERMINISTIC GRAPHICAL MODELS', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS183', course_title='INTRODUCTION TO COMPUTATIONAL BIOLOGY', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS184A', course_title='REPRESENTATIONS & ALGORITHMS FOR MOLECULAR BIOLOGY', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS184C', course_title='COMPUTATIONAL SYSTEMS BIOLOGY', units=4, course_level='Undergrad', combine_with=None),
        Courses(course_title_id='CS189', course_title='PROJECT IN BIOINFORMATICS', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS190', course_title='SPECIAL TOPICS IN INFORMATION & COMPUTER SCIENCE', units=4, course_level='Undergrad'),
        Courses(course_title_id='CS200S', course_title='SEMINAR IN COMPUTER SCIENCE RESEARCH', units=1, course_level='Grad'),
        Courses(course_title_id='CS201', course_title='FOUNDATIONS OF CRYPTOGRAPHIC PROTOCOLS', units=4, course_level='Grad'),
        Courses(course_title_id='CS202', course_title='APPLIED CRYPTOGRAPHY', units=4, course_level='Grad'),
        Courses(course_title_id='CS203', course_title='NETWORK & DISTRIBUTED SYSTEMS SECURITY', units=4, course_level='Grad'),
        Courses(course_title_id='CS204', course_title='USABLE SECURITY & PRIVACY', units=4, course_level='Grad'),
        Courses(course_title_id='CS205', course_title='COMPUTER SYSTEMS SECURITY', units=4, course_level='Grad'),
        Courses(course_title_id='CS206', course_title='PRINCIPLES OF SCIENTIFIC COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS211A', course_title='VISUAL COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS211B', course_title='ADVANCED TOPICS IN 3D COMPUTER GRAPHICS', units=4, course_level='Grad'),
        Courses(course_title_id='CS211C', course_title='NEW COURSE', units=4, course_level='Grad'),
        Courses(course_title_id='CS212', course_title='MULTIMEDIA SYSTEMS & APPLICATIONS', units=4, course_level='Grad'),
        Courses(course_title_id='CS213', course_title='INTRODUCTION TO VISUAL PERCEPTION', units=4, course_level='Grad'),
        Courses(course_title_id='CS216', course_title='IMAGE UNDERSTANDING', units=4, course_level='Grad'),
        Courses(course_title_id='CS217', course_title='LIGHT & GEOMETRY IN COMPUTER VISION', units=4, course_level='Grad'),
        Courses(course_title_id='CS219S', course_title='SEMINOR IN GRPHICS', units=2, course_level='Grad'),
        Courses(course_title_id='CS221', course_title='INFORMATION RETRIEVAL, FILTERING, & CLASSIFICATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS222', course_title='PRINCICPLES OF DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS223', course_title='TRANSACTION PROCESSING & DISTRIBUTED DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS224', course_title='TOPICS IN ADVANCED DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS225', course_title='NEXT GENERATION SEARCH SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS230', course_title='DISTRIBUTED COMPUTER SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS232', course_title='COMPUTER & COMMUNICATION NETWORKS', units=4, course_level='Grad'),
        Courses(course_title_id='CS233', course_title='NETWORKING LABORATORY', units=4, course_level='Grad'),
        Courses(course_title_id='CS234', course_title='ADVANCED NETWORKS', units=4, course_level='Grad'),
        Courses(course_title_id='CS236', course_title='WIRELESS & MOBILE NETWORKING', units=4, course_level='Grad'),
        Courses(course_title_id='CS237', course_title='MIDDLEWARE FOR NETWORKED & DISTRIBUTED SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS238', course_title='ADVANCED OPERATING SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS241', course_title='ADVANCED COMPILER CONSTRUCTION', units=4, course_level='Grad'),
        Courses(course_title_id='CS242', course_title='PARALLEL COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS243', course_title='HIGH-PERFORMANCE ARCHITECTURE & THEIR COMPILERS', units=4, course_level='Grad'),
        Courses(course_title_id='CS244', course_title='INTRODUCTION TO EMBEDDED & UBIQUITOUS SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS245', course_title='SOFTWARE FOR EMBEDDED SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS247', course_title='COMPLEX SYSTEMS SOFTWARE', units=4, course_level='Grad'),
        Courses(course_title_id='CS248A', course_title='INTRODUCTION TO UBIQUITOUS COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS248B', course_title='UBIQUITOUS COMPUTING & INTERACTION', units=4, course_level='Grad'),
        Courses(course_title_id='CS250A', course_title='COMPUTER SYSTEMS ARCHITECTURE', units=4, course_level='Grad'),
        Courses(course_title_id='CS250B', course_title='MODERN COMPUTER SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS252', course_title='INTRODUCTION TO COMPUTER DESIGN', units=4, course_level='Grad'),
        Courses(course_title_id='CS253', course_title='ANALYSIS OF PROGRAMMING LANGUAGES', units=4, course_level='Grad'),
        Courses(course_title_id='CS259S', course_title='SEMINAR IN DESIGN SCIENCE', units=2, course_level='Grad'),
        Courses(course_title_id='CS260', course_title='FUNDAMENTALS OF THE DESIGN & ANALYSIS OF ALGORITHMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS261', course_title='DATA STRUCTURES', units=4, course_level='Grad'),
        Courses(course_title_id='CS262', course_title='COMPUTATIONAL COMPLEXITY', units=4, course_level='Grad'),
        Courses(course_title_id='CS263', course_title='ANALYSIS OF ALGORITHMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS264', course_title='QUANTUM COMPUTATION & INFORMATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS265', course_title='GRAPH ALGORITHMS', units=4, course_level='Grad', combine_with='CS163'),
        Courses(course_title_id='CS266', course_title='COMPUTATIONAL GEOMETRY', units=4, course_level='Grad'),
        Courses(course_title_id='CS268', course_title='INTRODUCTION TO OPTIMIZATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS269S', course_title='SEMINAR IN THE THEORY OF ALGORITHMS & DATA STRUCTURES', units=2, course_level='Grad'),
        Courses(course_title_id='CS271', course_title='INTRODUCTION TO ARTIFICIAL INTELLIGENCE', units=4, course_level='Grad'),
        Courses(course_title_id='CS272', course_title='STATISTICAL NATURAL LANGUAGE PROCESSING', units=4, course_level='Grad'),
        Courses(course_title_id='CS273A', course_title='MACHINE LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS274A', course_title='PROBABILISTIC LEARNING: THEORY & ALGORITHMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS274B', course_title='LEARNING IN GRAPHICAL MODELS', units=4, course_level='Grad'),
        Courses(course_title_id='CS274C', course_title='NEURAL NETWORKS & DEEP LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS274D', course_title='ARTIFICIAL INTELLIGENCE FRONTIERS: TECHNICAL, ETHICAL, AND SOCIETAL', units=4, course_level='Grad'),
        Courses(course_title_id='CS274E', course_title='DEEP GENERATIVE MODELS', units=4, course_level='Grad'),
        Courses(course_title_id='CS275', course_title='NETWORK-BASED REASONING/ CONSTRAINT NETWORKS', units=4, course_level='Grad'),
        Courses(course_title_id='CS276', course_title='NETWORK-BASED REASONING/ BELIEF NETWORKS', units=4, course_level='Grad'),
        Courses(course_title_id='CS277', course_title='CONTROL AND REINFORCEMENT LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS278', course_title='PROBABILITY MODELS', units=4, course_level='Grad'),
        Courses(course_title_id='CS284A', course_title='REPRESENTATIONS & ALGORITHMS FOR MOLECULAR BIOLOGY', units=4, course_level='Grad'),
        Courses(course_title_id='CS284C', course_title='COMPUTATIONAL SYSTEMS BIOLOGY', units=4, course_level='Grad'),
        Courses(course_title_id='CS285', course_title='MATHEMATICAL & COMPUTATIONAL BIOLOGY', units=4, course_level='Grad'),
        Courses(course_title_id='CS290', course_title='RESEARCH SEMINAR', units=2, course_level='Grad'),
        Courses(course_title_id='CS295', course_title='SPECIAL TOPICS', units=4, course_level='Grad'),
        Courses(course_title_id='CS296', course_title='ELEMENTS OF SCIENTIFIC WRITING', units=4, course_level='Grad'),
        Courses(course_title_id='CS201P', course_title='INTRO TO COMPUTER SECURITY', units=4, course_level='Grad'),
        Courses(course_title_id='CS202P', course_title='APPLIED CRYPTOGRAPHY', units=4, course_level='Grad'),
        Courses(course_title_id='CS203P', course_title='NETWORK & DISTRIBUTED SYSTEMS SECURITY', units=4, course_level='Grad'),
        Courses(course_title_id='CS206P', course_title='PRINCIPLES OF SCIENTIFIC COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS210P', course_title='COMPUTER GRAPHICS & VISUALIZATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS211P', course_title='VISUAL COMPUTING', units=4, course_level='Grad'),
        Courses(course_title_id='CS220P', course_title='DATABASES & DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS222P', course_title='PRINCIPLES OF DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS223P', course_title='TRANSACTION PROCESSING & DIST. DATA MGMT', units=4, course_level='Grad'),
        Courses(course_title_id='CS224P', course_title='BIG DATA MANAGEMENT', units=4, course_level='Grad'),
        Courses(course_title_id='CS230P', course_title='DISTRIBUTED COMPUTER SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS231P', course_title='PARALLEL AND DISTRIBUTED COMPUTING FOR PROFESSIONALS', units=4, course_level='Grad'),
        Courses(course_title_id='CS232P', course_title='COMPUTER & COMMUNICATION NETWORKS', units=4, course_level='Grad'),
        Courses(course_title_id='CS238P', course_title='OPERATING SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS242P', course_title='COMPILERS & INTERPRETERS', units=4, course_level='Grad'),
        Courses(course_title_id='CS244P', course_title='INTRODUCTION TO EMBEDDED & UBIQUITOUS SYSTEMS', units=4, course_level='Grad'),
        Courses(course_title_id='CS250P', course_title='COMPUTER SYSTEMS ARCHITECTURE', units=4, course_level='Grad'),
        Courses(course_title_id='CS253P', course_title='ADVANCED PROGRAMMING & PROBLEM SOLVING', units=4, course_level='Grad'),
        Courses(course_title_id='CS260P', course_title='FUNDAMENTALS OF ALGORITHMS WITH APPLICATIONS', units=4, course_level='Grad'),
        Courses(course_title_id='CS261P', course_title='DATA STRUCTURES', units=4, course_level='Grad'),
        Courses(course_title_id='CS262P', course_title='AUTOMATA & GRAMMARS', units=4, course_level='Grad'),
        Courses(course_title_id='CS267P', course_title='DATA COMPRESSION', units=4, course_level='Grad'),
        Courses(course_title_id='CS268P', course_title='INTRODUCTION TO OPTIMIZATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS271P', course_title='INTRODUCTION TO ARTIFICIAL INTELLIGENCE', units=4, course_level='Grad'),
        Courses(course_title_id='CS273P', course_title='MACHINE LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS274P', course_title='NEURAL NETWORKS & DEEP LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS275P', course_title='GRAPHICAL MODELS & STATISTICAL LEARNING', units=4, course_level='Grad'),
        Courses(course_title_id='CS294P', course_title='KEYSTONE COMMUNICATION', units=4, course_level='Grad'),
        Courses(course_title_id='CS295P', course_title='KEYSTONE PROJECT', units=4, course_level='Grad'),
        Courses(course_title_id='CS296P', course_title='CAPSTONE PROFESSIONAL WRITING FOR COMPUTER SCIENCE CAREERS', units=4, course_level='Grad'),
        Courses(course_title_id='CS297P', course_title='CAPSTONE DESIGN PROJECT FOR COMPUTER SCIENCE', units=4, course_level='Grad'),
        Courses(course_title_id='CS298P', course_title='THESIS SUPERVISION', units=2, course_level='Grad'),
        Courses(course_title_id='CS299P', course_title='INDIVIDUAL STUDY', units=2, course_level='Grad'),
        Courses(course_title_id='CSE90', course_title='SYSTEMS ENGINEERING ETHICS & TECHNICAL COMMUNICATIONS', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICS3', course_title='INTERNET TECHNOLOGIES & THEIR SOCIAL IMPACT', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS4', course_title='HUMAN FACTORS FOR THE WEB', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS6N', course_title='COMPUTATIONAL LINEAR ALGEBRA', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS7', course_title='INTRODUCING MODERN COMPUTATIONAL TOOLS', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS9', course_title='Intro to Computation for Scientists and Engineers', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS10', course_title='HOW COMPUTERS WORK', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS11', course_title='THE INTERNET & PUBLIC POLICY', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS20', course_title='INVITATION TO COMPUTING', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS31', course_title='INTRODUCTION TO PROGRAMMING', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS33', course_title='INTERMEDIATE PROGRAMMING', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS45J', course_title='PROGRAMMING IN JAVA AS A SECOND LANGUAGE', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS46', course_title='DATA STRUCTURE IMPLEMENTATION & ANALYSIS', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS51', course_title='INTRODUCTORY COMPUTER ORGANIZATION', units=6, course_level='Undergrad'),
        Courses(course_title_id='ICS53', course_title='PRINCIPLES IN SYSTEM DESIGN', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS53L', course_title='PRINCIPLES IN SYSTEM DESIGN LIBRARY', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICS61', course_title='GAME SYSTEMS & DESIGN', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS62', course_title='GAME TECHNOLOGIES & INTERACTIVE MEDIA', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS80', course_title='ENTREPRENEURSHIP', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICS90', course_title='NEW STUDENTS SEMINAR', units=1, course_level='Undergrad'),
        Courses(course_title_id='ICS161', course_title='GAME ENGINE LAB', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS162', course_title='MODELING & WORLD BUILDING', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS163', course_title='MOBILE & UBIQUITOUS GAMES', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS166', course_title='GAME DESIGN', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS167', course_title='MULTIPLAYER GAME SYSTEMS', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS168', course_title='MULTIPLAYER GAME PROJECT', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS169A', course_title='CAPSTONE GAME PROJECT I', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS169B', course_title='CAPSTONE GAME PROJECT II', units=4, course_level='Undergrad'),
        Courses(course_title_id='ICS192', course_title='INDUSTRIAL OR PUBLIC SECTOR FIELD STUDY', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICS193', course_title='TUTORING IN ICS', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICSH197', course_title='HONORS SEMINAR', units=2, course_level='Undergrad'),
        Courses(course_title_id='ICS290', course_title='ENTREPRENEURSHIP', units=4, course_level='Grad'),
        Courses(course_title_id='ICS398A', course_title='TEACHING ASSISTANT TRAINING SEMINAR', units=2, course_level='Grad'),
        Courses(course_title_id='ICS398B', course_title='ADVANCED TEACHING ASSISTANT SEMINAR', units=4, course_level='Grad'),
        Courses(course_title_id='ICS399', course_title='UNIVERSITY TEACHING', units=4, course_level='Grad'),
        Courses(course_title_id='CS 199', course_title='INDEPENDENT STUDY', units=2, course_level='Grad'),
        Courses(course_title_id='CS 260S', course_title='SEMINAR', units=1, course_level='Grad'),
        Courses(course_title_id='STATS 170A', course_title='Project in Data Science I', units=4, course_level='Undergrad'),
        Courses(course_title_id='STATS 170B', course_title='Project in Data Science II', units=4, course_level='Undergrad')
    ]

    db.session.bulk_save_objects(courses)
    db.session.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    db.drop_all()
    db.create_all()
    init_rules()
    init_courses()
    
    click.echo('Initialized the database.')


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'     
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.cli.add_command(init_db_command)

    app.register_blueprint(auth)
    app.register_blueprint(faculty) # temporarily render faculty views under url_prefix='/faculty'
    app.register_blueprint(logs) # temporarily render logs views under exception tab with url_prefix='/logs'
    app.register_blueprint(settings) # temporarily render settings views under url_prefix='/settings'
    app.register_blueprint(courses)


    @app.route('/')
    def redirect_to_auth_login():
        return redirect('/auth')

    return app