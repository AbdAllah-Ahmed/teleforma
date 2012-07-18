from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from telemeta.models import *
from telemeta.util.unaccent import unaccent
from teleforma.models import *
import logging
import os


class Logger:
    """A logging object"""

    def __init__(self, file):
        self.logger = logging.getLogger('myapp')
        self.hdlr = logging.FileHandler(file)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(self.formatter)
        self.logger.addHandler(self.hdlr)
        self.logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Import conferences from the MEDIA_ROOT directory "
    admin_email = 'webmaster@parisson.com'
    args = 'organization'
    spacer = '_-_'
    formats = ['mp3', 'webm']
    logger = logging.getLogger('myapp')
    hdlr = logging.FileHandler('/tmp/import.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    def handle(self, *args, **options):
        organization_name = args[0]
        organization = Organization.objects.get(name=organization_name)
        self.media_dir = settings.MEDIA_ROOT + organization.name
        file_list = []
        all_conferences = Conference.objects.all()
        i = 1
        #FIXME:
        #medias = Media.objects.all()
        #for media in medias:
        #    media.delete()
        #items = MediaItem.objects.all()
        #for item in items:
        #    item.delete()

        for root, dirs, files in os.walk(self.media_dir):
            for filename in files:
                name = os.path.splitext(filename)[0]
                ext = os.path.splitext(filename)[1][1:]

                if ext in self.formats:
                    path = root + os.sep + filename
                    root_list = root.split(os.sep)
                    public_id = root_list[-1]
                    course = root_list[-2]
                    course_id = course.split(self.spacer)[0]
                    course_type = course.split(self.spacer)[1].lower()
                    date = root_list[-3]
                    department_name = root_list[-4]
                    organization_name = root_list[-5]
                    path = os.sep.join(root_list[-5:]) + os.sep + filename

                    department, created = Department.objects.get_or_create(name=department_name, organization=organization)
                    conference, created = Conference.objects.get_or_create(public_id=public_id)

                    exist = False
                    medias = conference.media.all()
                    for media in medias:
                        items = media.items.filter(file=path)
                        if items:
                            exist = True
                            break

                    streaming = False
                    try:
                        stations = conference.station.filter(started=True)
                        ids = [station.public_id for station in stations]
                        for id in ids:
                            if id == public_id:
                                streaming = True
                    except:
                        pass

                    if not exist and not streaming:
                        print path
                        collection_id = '_'.join([department_name, course_id, course_type])
                        collections = MediaCollection.objects.filter(code=collection_id)
                        if not collections:
                            collection = MediaCollection(code=collection_id,title=collection_id)
                            collection.save()
                        else:
                            collection = collections[0]

                        id = '_'.join([collection_id, public_id, ext, str(i)])

                        items = MediaItem.objects.filter(collection=collection, code=id)
                        if not items:
                            item = MediaItem(collection=collection, code=id)
                            item.save()
                        else:
                            item = items[0]

                        item.title = name
                        item.file = path
                        item.save()
                        media, c = Media.objects.get_or_create(conference=conference)
                        media.items.add(item)
                        media.course = conference.course
                        media.course_type = conference.course_type
                        media.save()
                        self.logger.info('Imported: ' + path)
                        i += 1

