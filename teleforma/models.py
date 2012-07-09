#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   teleforma

   Copyright (c) 2006-2012 Guillaume Pellerin <yomguy@parisson.com>

# This software is governed by the CeCILL  license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".

# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.

# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.

# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

# Author: Guillaume Pellerin <yomguy@parisson.com>
"""

import os
import re
import pwd
import time
import urllib
import string
import datetime
import mimetypes
import telemeta
import django.db.models as models
from django.db.models import *
from django.forms import ModelForm, TextInput, Textarea
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from teleforma.fields import *
from django.contrib.contenttypes import generic
from notes.models import Note
import jqchat.models
from django.core.paginator import InvalidPage, EmptyPage
from django.template.defaultfilters import slugify

app_label = 'teleforma'

n_sessions = 21
session_choices = [(str(x), str(y)) for x in range(1, n_sessions) for y in range(1, n_sessions) if x == y]
server_choices = [('icecast', 'icecast'), ('stream-m', 'stream-m')]
streaming_choices = [('mp3', 'mp3'), ('ogg', 'ogg'), ('webm', 'webm'), ('mp4', 'mp4')]


class Organization(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = app_label + '_' + 'organization'
        verbose_name = _('organization')

class Department(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)
    organization    = ForeignKey('Organization', related_name='department',
                                 verbose_name=_('organization'))

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.__unicode__())

    class Meta:
        db_table = app_label + '_' + 'department'
        verbose_name = _('department')


class Period(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = app_label + '_' + 'period'
        verbose_name = _('period')

class CourseType(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = app_label + '_' + 'course_type'
        verbose_name = _('course type')

class Course(Model):

    department      = ForeignKey('Department', related_name='course',
                                 verbose_name=_('department'))
    title           = CharField(_('title'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)
    code            = CharField(_('code'), max_length=255)
    date_modified   = DateTimeField(_('date modified'), auto_now=True)
    number          = IntegerField(_('number'), blank=True, null=True)
    synthesis_note  = BooleanField(_('synthesis note'))
    obligation      = BooleanField(_('obligations'))
    magistral       = BooleanField(_('magistral'))

    notes = generic.GenericRelation(Note)

    def __unicode__(self):
        return self.title

    @property
    def slug(self):
        return slugify(self.__unicode__())

    class Meta:
        db_table = app_label + '_' + 'course'
        verbose_name = _('course')
        ordering = ['number']


class Professor(Model):

    user            = ForeignKey(User, related_name='professor', verbose_name=_('user'), unique=True)
    courses         = ManyToManyField('Course', related_name="professor", verbose_name=_('courses'),
                                        blank=True, null=True)

    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name

    class Meta:
        db_table = app_label + '_' + 'professor'
        verbose_name = _('professor')


class Room(Model):

    organization    = ForeignKey('Organization', related_name='room', verbose_name=_('organization'))
    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.organization.name + ' - ' + self.name

    class Meta:
        db_table = app_label + '_' + 'room'
        verbose_name = _('room')


class Conference(Model):

    public_id       = CharField(_('public_id'), max_length=255, blank=True)
    course          = ForeignKey('Course', related_name='conference', verbose_name=_('course'))
    course_type     = ForeignKey('CourseType', related_name='conference', verbose_name=_('course type'))
    professor       = ForeignKey('Professor', related_name='conference', verbose_name=_('professor'),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    session         = CharField(_('session'), choices=session_choices,
                                      max_length=16, default="1")
    room            = ForeignKey('Room', related_name='conference', verbose_name=_('room'),
                                 null=True, blank=True)
    comment         = CharField(_('comment'), max_length=255, blank=True)
    date_begin      = DateTimeField(_('begin date'), null=True, blank=True)
    date_end        = DateTimeField(_('end date'), null=True, blank=True)
    readers         = ManyToManyField(User, related_name="conference", verbose_name=_('readers'),
                                        blank=True, null=True)

    notes = generic.GenericRelation(Note)

    @property
    def description(self):
        return ' - '.join([self.course.department.name, self.course.title, self.course_type.name,
                           self.session, self.professor.user.first_name, self.professor.user.last_name,
                           str(self.date_begin)])

    def __unicode__(self):
        return self.description

    def save(self, **kwargs):
        super(Conference, self).save(**kwargs)
        self.course.save()

    def to_dict(self):
        dict = [{'id':'public_id','value': self.public_id, 'class':'', 'label':'public_id'},
                {'id':'organization','value': self.organization, 'class':'', 'label':'Organization'},
                {'id': 'department', 'value': self.department , 'class':'', 'label':'Department'},
                {'id' : 'conference', 'value': self.conference, 'class':'' , 'label': 'Conference'},
                {'id': 'professor', 'value': self.professor, 'class':'' , 'label': 'Professor'},
                {'id': 'session', 'value': self.session, 'class':'' , 'label': 'Session'},
                {'id': 'comment', 'value': self.comment, 'class':'' , 'label': 'Comment'},
                {'id': 'started', 'value': str(self.started), 'class':'' , 'label': 'Started'},
                ]
        return dict

    class Meta:
        db_table = app_label + '_' + 'conference'
        verbose_name = _('conference')
        ordering = ['-date_begin']


class StreamingServer(Model):

    element_type = 'streamingserver'

    host            = CharField(_('host'), max_length=255)
    port            = CharField(_('port'), max_length=32)
    type            = CharField(_('type'), choices=server_choices, max_length=32)
    description     = CharField(_('description'), max_length=255, blank=True)
    source_password = CharField(_('source password'), max_length=32)
    admin_password  = CharField(_('admin password'), max_length=32, blank=True)

    def __unicode__(self):
        return self.host + ':' + self.port + ' - ' + self.type

    class Meta:
        db_table = app_label + '_' + 'streaming_server'
        verbose_name = _('streaming server')


class LiveStream(Model):

    element_type = 'livestream'

    course          = ForeignKey('Course', related_name='livestream',
                                 verbose_name=_('course'))
    course_type     = ForeignKey('CourseType', related_name='livestream',
                                 verbose_name=_('course type'),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    conference      = ForeignKey('Conference', related_name='livestream',
                                verbose_name=_('conference'),
                                blank=True, null=True, on_delete=models.SET_NULL)
    server     = ForeignKey('StreamingServer', related_name='livestream',
                                verbose_name=_('streaming server'))
    stream_type = CharField(_('Streaming type'),
                            choices=streaming_choices, max_length=32)
    streaming       = BooleanField(_('streaming'))

    @property
    def slug(self):
        slug = '-'.join([self.course.department.slug, self.course.slug,
                         self.course_type.name.lower()])
        return slug

    @property
    def mount_point(self):
        if self.server.type == 'stream-m':
            return  'consume/' + self.slug
        else:
            return self.slug + '.' + self.stream_type

    @property
    def snapshot_url(self):
        url = ''
        if self.server.type == 'stream-m':
            url = 'http://' + self.server.host + ':' + self.server.port + \
                    '/snapshot/' + self.slug
        return url

    @property
    def url(self):
        return 'http://' + self.server.host + ':' + self.server.port + '/' + self.mount_point

    def __unicode__(self):
        if self.conference:
            return self.conference.description
        else:
            return self.slug

    class Meta:
        db_table = app_label + '_' + 'live_stream'
        verbose_name = _('live stream')


class MediaBase(Model):
    "Base media resource"

    title           = CharField(_('title'), max_length=255, blank=True)
    description     = CharField(_('description'), max_length=255, blank=True)
    credits         = CharField(_('credits'), max_length=255, blank=True)
    date_added      = DateTimeField(_('date added'), auto_now_add=True)
    date_modified   = DateTimeField(_('date modified'), auto_now=True)
    code            = CharField(_('code'), max_length=255, blank=True)
    is_published    = BooleanField(_('published'))

    notes = generic.GenericRelation(Note)

    def get_fields(self):
        return self._meta.fields

    class Meta:
        abstract = True


class DocumentType(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)
    number          = IntegerField(_('number'), blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = app_label + '_' + 'document_type'
        verbose_name = _('document type')
        ordering = ['number']


class Document(MediaBase):

    element_type = 'document'

    course          = ForeignKey('Course', related_name='document', verbose_name=_('course'))
    course_type     = ManyToManyField('CourseType', related_name='document',
                                      verbose_name=_('course type'), blank=True, null=True)
    conference      = ForeignKey('Conference', related_name='document', verbose_name=_('conference'),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    type            = ForeignKey('DocumentType', related_name='document', verbose_name=_('type'),
                                 blank=True, null=True)
    is_annal        = BooleanField(_('annal'))
    file            = FileField(_('file'), upload_to='items/%Y/%m/%d', db_column="filename", blank=True)
    readers         = ManyToManyField(User, related_name="document", verbose_name=_('readers'),
                                        blank=True, null=True)

    def is_image(self):
        is_url_image = False
        if self.url:
            url_types = ['.png', '.jpg', '.gif', '.jpeg']
            for type in url_types:
                if type in self.url or type.upper() in self.url:
                    is_url_image = True
        return 'image' in self.mime_type or is_url_image

    def set_mime_type(self):
        if self.file:
            self.mime_type = mimetypes.guess_type(self.file.path)[0]

    def __unicode__(self):
        types = ' - '.join([unicode(t) for t in self.course_type.all()])
        return  ' - '.join([unicode(self.course), unicode(types), self.title ])

    def set_read(self, user):
        pass

    def get_read(self, user):
        return user in self.readers

    def save(self, **kwargs):
        super(Document, self).save(**kwargs)
        self.course.save()

    class Meta:
        db_table = app_label + '_' + 'document'
        ordering = ['-date_added']


class Media(MediaBase):
    "Describe a media resource linked to a conference and a telemeta item"

    element_type = 'media'

    course          = ForeignKey('Course', related_name='media', verbose_name=_('course'))
    course_type     = ForeignKey('CourseType', related_name='media', verbose_name=_('course type'))
    conference      = ForeignKey('Conference', related_name='media', verbose_name=_('conference'),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    item            = ForeignKey(telemeta.models.media.MediaItem, related_name='media',
                                 verbose_name='item', blank=True, null=True)
    is_live         = BooleanField(_('is live'))
    readers         = ManyToManyField(User, related_name="media", verbose_name=_('readers'),
                                        blank=True, null=True)

    def __unicode__(self):
        description = self.course.title
        if self.item:
            return description + ' _ ' + self.item.title
        else:
            return description

    def save(self, **kwargs):
        super(Media, self).save(**kwargs)
        self.course.save()

    class Meta:
        db_table = app_label + '_' + 'media'
        ordering = ['-date_modified']


# STUDENT

class IEJ(Model):

    name            = CharField(_('name'), max_length=255)
    description     = CharField(_('description'), max_length=255, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = app_label + '_' + 'iej'
        verbose_name = _('IEJ')
        verbose_name_plural = _('IEJ')
        ordering = ['name']


class Training(Model):

    code            = CharField(_('code'), max_length=255)
    name            = CharField(_('name'), max_length=255, blank=True)
    period          = ForeignKey('Period', related_name='training', verbose_name=_('period'),
                                 blank=True, null=True)
    synthesis_note  = ManyToManyField('CourseType', related_name="training_synthesis_note",
                                        verbose_name=_('synthesis note'),
                                        blank=True, null=True)
    obligation      = ManyToManyField('CourseType', related_name="training_obligation",
                                        verbose_name=_('obligations'),
                                        blank=True, null=True)
    procedure       = ManyToManyField('CourseType', related_name="training_procedure",
                                        verbose_name=_('procedure'),
                                        blank=True, null=True)
    written_speciality = ManyToManyField('CourseType', related_name="training_written_speciality",
                                        verbose_name=_('written speciality'),
                                        blank=True, null=True)
    oral_speciality = ManyToManyField('CourseType', related_name="training_oral_speciality",
                                        verbose_name=_('oral speciality'),
                                        blank=True, null=True)
    oral_1          = ManyToManyField('CourseType', related_name="training_oral_1",
                                        verbose_name=_('oral 1'),
                                        blank=True, null=True)
    oral_2          = ManyToManyField('CourseType', related_name="training_oral_2",
                                        verbose_name=_('oral 2'),
                                        blank=True, null=True)
    options         = ManyToManyField('CourseType', related_name="training_options",
                                        verbose_name=_('options'),
                                        blank=True, null=True)
    magistral       = ManyToManyField('CourseType', related_name="training_magistral",
                                        verbose_name=_('magistral'),
                                        blank=True, null=True)
    cost            = FloatField(_('cost'), blank=True, null=True)

    def __unicode__(self):
        code = self.code
        if self.period:
            code += ' - ' + self.period.name
        return code

    class Meta:
        db_table = app_label + '_' + 'training'
        verbose_name = _('training')


class Student(Model):

    user            = ForeignKey(User, related_name='student', verbose_name=_('user'), unique=True )
    period          = ManyToManyField('Period', related_name='student', verbose_name=_('period'),
                                  blank=True, null=True)
    iej             = ForeignKey('IEJ', related_name='student', verbose_name=_('iej'),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    training        = ForeignKey('Training', related_name='student', verbose_name=_('training'))
    platform_only   = BooleanField(_('platform only'))
    procedure       = ForeignKey('Course', related_name="procedure",
                                        verbose_name=_('procedure'),
                                        blank=True, null=True)
    written_speciality = ForeignKey('Course', related_name="written_speciality",
                                        verbose_name=_('written speciality'),
                                        blank=True, null=True)
    oral_speciality = ForeignKey('Course', related_name="oral_speciality",
                                        verbose_name=_('oral speciality'),
                                        blank=True, null=True)
    oral_1          = ForeignKey('Course', related_name="oral_1", verbose_name=_('oral 1'),
                                        blank=True, null=True)
    oral_2          = ForeignKey('Course', related_name="oral_2", verbose_name=_('oral 2'),
                                        blank=True, null=True)
    options          = ForeignKey('Course', related_name="options", verbose_name=_('options'),
                                        blank=True, null=True)

    def __unicode__(self):
        try:
            return self.user.last_name + ' ' + self.user.first_name
        except:
            return ''

    class Meta:
        db_table = app_label + '_' + 'student'
        verbose_name = _('student')
        ordering = ['user__last_name']


class Profile(models.Model):
    "User profile extension"

    user            = ForeignKey(User, related_name='profile', verbose_name=_('user'), unique=True)
    address         = TextField(_('Address'), blank=True)
    postal_code     = CharField(_('Postal code'), max_length=255, blank=True)
    city            = CharField(_('City'), max_length=255, blank=True)
    country         = CharField(_('Country'), max_length=255, blank=True)
    language        = CharField(_('Language'), max_length=255, blank=True)
    telephone       = CharField(_('Telephone'), max_length=255, blank=True)
    expiration_date = DateField(_('Expiration_date'), blank=True, null=True)
    init_password   = BooleanField(_('Password initialized'))

    class Meta:
        db_table = app_label + '_' + 'profiles'
        verbose_name = _('profile')


class Payment(models.Model):
    "Student payment"

    student = ForeignKey(Student, related_name="payment", verbose_name=_('student'))
    amount  = FloatField(_('amount'))
    date_added = DateTimeField(_('date added'), auto_now_add=True)

    def __unicode__(self):
        return ' - '.join([str(self.date_added), self.student.user.last_name + ' ' + \
                        self.student.user.first_name,  str(self.amount)])

    class Meta:
        db_table = app_label + '_' + 'payment'
        verbose_name = _('payment')
        ordering = ['-date_added']


# TOOLS
class NamePaginator(object):
    """Pagination for string-based objects"""

    def __init__(self, object_list, on=None, per_page=25):
        self.object_list = object_list
        self.count = len(object_list)
        self.pages = []

        # chunk up the objects so we don't need to iterate over the whole list for each letter
        chunks = {}

        for obj in self.object_list:
            if on:
                obj_str = getattr(obj, on).encode('utf8')
            else:
                obj_str = obj.encode('utf8')

            if len(obj_str):
                letter = str.upper(obj_str[0])
            else:
                letter = ''

            if letter not in chunks:
                chunks[letter] = []

            chunks[letter].append(obj)

        # the process for assigning objects to each page
        current_page = NamePage(self)

        for letter in string.ascii_uppercase:
            if letter not in chunks:
                current_page.add([], letter)
                continue

            sub_list = chunks[letter] # the items in object_list starting with this letter

            new_page_count = len(sub_list) + current_page.count
            # first, check to see if sub_list will fit or it needs to go onto a new page.
            # if assigning this list will cause the page to overflow...
            # and an underflow is closer to per_page than an overflow...
            # and the page isn't empty (which means len(sub_list) > per_page)...
            if new_page_count > per_page and \
                    abs(per_page - current_page.count) < abs(per_page - new_page_count) and \
                    current_page.count > 0:
                # make a new page
                self.pages.append(current_page)
                current_page = NamePage(self)

            current_page.add(sub_list, letter)

        # if we finished the for loop with a page that isn't empty, add it
        if current_page.count > 0: self.pages.append(current_page)

    def page(self, num):
        """Returns a Page object for the given 1-based page number."""
        if len(self.pages) == 0:
            return None
        elif num > 0 and num <= len(self.pages):
            return self.pages[num-1]
        else:
            raise InvalidPage

    @property
    def num_pages(self):
        """Returns the total number of pages"""
        return len(self.pages)

class NamePage(object):
    def __init__(self, paginator):
        self.paginator = paginator
        self.object_list = []
        self.letters = []

    @property
    def count(self):
        return len(self.object_list)

    @property
    def start_letter(self):
        if len(self.letters) > 0:
            self.letters.sort(key=str.upper)
            return self.letters[0]
        else: return None

    @property
    def end_letter(self):
        if len(self.letters) > 0:
            self.letters.sort(key=str.upper)
            return self.letters[-1]
        else: return None

    @property
    def number(self):
        return self.paginator.pages.index(self) + 1

    def add(self, new_list, letter=None):
        if len(new_list) > 0:
            self.object_list = self.object_list + new_list
        if letter:
            self.letters.append(letter)

    def __repr__(self):
        if self.start_letter == self.end_letter:
            return self.start_letter
        else:
            return '%c-%c' % (self.start_letter, self.end_letter)

