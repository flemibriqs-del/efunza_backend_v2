from django.core.management.base import BaseCommand
from api.models import Program, Lesson, Video, ContentItem, Assessment, GenericResource, Book

PROGRAMS = [
    ('E-Readathon','e-readathon','Reading & Literacy','AI reading coach',88,'Reading quests','Literacy and communication'),
    ('E-Lab','e-lab','STEM & Science','AI lab assistant',93,'Experiment missions','Science and engineering'),
    ('Codecrafters','codecrafters','Programming & Technology','AI coding tutor',95,'Algorithm quests','Software, AI and data'),
    ('Kidpreneurs','kidpreneurs','Business & Entrepreneurship','AI business mentor',90,'Startup missions','Entrepreneurship'),
    ('Ink Ventors','ink-ventors','Creative Writing','AI writing assistant',87,'Writing quests','Writing and media'),
    ('Artful Minds','artful-minds','Arts & Creativity','AI creativity guide',86,'Design quests','Design and creative arts'),
    ('Robokids','robokids','Robotics & Engineering','AI robotics mentor',94,'Robot missions','Robotics and IoT'),
    ('Young Orators','young-orators','Public Speaking','AI speech coach',84,'Speech quests','Leadership and communication'),
    ('EcoHeroes','ecoheroes','Environmental Science','AI sustainability guide',96,'Eco missions','Climate and sustainability'),
    ('Melody Masters','melody-masters','Music & Performance','AI music coach',82,'Rhythm quests','Music and performance'),
    ('Stage Stars','stage-stars','Drama & Acting','AI performance coach',83,'Acting quests','Drama and production'),
    ('Math Adventure','math-adventure','Mathematics','AI math tutor',92,'Math quests','STEM and analytics'),
    ('Bonjour Kids','bonjour-kids','Language Learning','AI French coach',81,'French quests','Global communication'),
    ('Kinderlingo','kinderlingo','Language Learning','AI German coach',81,'German quests','Global communication'),
    ('Safari Swahili','safari-swahili','Language Learning','AI Kiswahili coach',85,'Kiswahili quests','Culture and communication'),
]

class Command(BaseCommand):
    help='Seed all Efunza E²IO-aligned programs and demo content'

    def handle(self,*args,**kwargs):
        for index,(title,slug,category,ai_feature,e2io_score,quest,career) in enumerate(PROGRAMS, start=1):
            program, _ = Program.objects.update_or_create(
                slug=slug,
                defaults={
                    'title':title,
                    'description':f'{title} is an E²IO-upgraded Efunza program combining core learning, AI support, gamification, student intelligence, labs, and career pathways.',
                    'category':category,
                    'price':0 if index in [1,5,9] else 2999,
                    'is_active':True,
                    'metadata':{
                        'e2io_score':e2io_score,
                        'ai_feature':ai_feature,
                        'gamification':[quest,'XP','Badges','Streaks'],
                        'intelligence':['Student analytics','Weak-topic detection','Recommendation engine','Predictive performance','Career guidance AI'],
                        'labs':['Efunza Lab','E²IO Project Pathway'],
                        'career_pathways':[career],
                    }
                }
            )
            Lesson.objects.get_or_create(program=program,title=f'Welcome to {title}',topic='Orientation',defaults={'content':f'Introduction to {title} and the E²IO learning pathway.', 'order':1})
            Lesson.objects.get_or_create(program=program,title=f'{title} AI + Gamified Challenge',topic='Gamification',defaults={'content':f'Complete missions, earn XP and use {ai_feature} to improve your skills.', 'order':2})
            GenericResource.objects.get_or_create(resource_type='lab_project',title=f'{title} E²IO Lab Project',defaults={'summary':f'A project pathway for applying {title} skills to real-world problems.', 'data':{'program_slug':slug,'career_pathway':career}, 'status':'open'})
        Video.objects.get_or_create(title='Welcome to Efunza',topic='Orientation',url='https://example.com/video')
        ContentItem.objects.get_or_create(title='Project-Based Learning Guide',content_type='article',body='Build real projects while learning.')
        Assessment.objects.get_or_create(title='Algorithms Quiz',topic='Algorithms',questions=[{'q':'What is an algorithm?','choices':['A step-by-step solution','A phone','A battery'],'answer':0}])
        self.stdout.write(self.style.SUCCESS('All 15 Efunza programs seeded.'))
