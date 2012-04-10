# -*- coding: utf-8 -*-
# Copyright (c) 2007-2012 Parisson SARL

# This software is a computer program whose purpose is to backup, analyse,
# transcode and stream any audio content with its metadata over a web frontend.

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
#
# Authors: Guillaume Pellerin <yomguy@parisson.com>

import os.path
from django.conf.urls.defaults import *
from django.views.generic import *
from django.views.generic.base import *
from teleforma.models import *
from teleforma.views import *
from jsonrpc import jsonrpc_site
import jqchat.views

htdocs_forma = os.path.dirname(__file__) + '/htdocs'
user_export = UsersXLSExport()

urlpatterns = patterns('',

    # Telemeta
    url(r'^', include('telemeta.urls')),

    url(r'^desk/courses/$', CoursesView.as_view(), name="teleforma-courses"),
    url(r'^desk/courses/(?P<pk>.*)$', CourseView.as_view(), name="teleforma-course-detail"),
    url(r'^desk/medias/(?P<pk>.*)$', MediaView.as_view(), name="teleforma-media-detail"),
    url(r'^desk/documents/(?P<pk>.*)/download/', document_download, name="teleforma-document-download"),
    url(r'^desk/documents/(?P<pk>.*)/view/', document_view, name="teleforma-document-view"),

    # Postman
    url(r'^messages/', include('postman.urls')),

    # Users
    url(r'^all_users/$', UsersView.as_view(), name="teleforma-users"),
    url(r'^all_users/by_trainings/(\w+)$', UsersTrainingView.as_view(), name="teleforma-training-users"),
    url(r'^all_users/export/$', user_export.export, name="teleforma-users-xls-export"),
    url(r'^all_users/by_trainings/(\w+)/export/$', user_export.export_training, name="teleforma-training-users-export"),

# CSS+Images (FIXME: for developement only)
    url(r'^teleforma/css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': htdocs_forma+'/css'},
        name="teleforma-css"),
    url(r'images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': htdocs_forma+'/images'},
        name="teleforma-images"),
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': htdocs_forma+'/js'},
        name="teleforma-js"),

# JSON RPC
    url(r'json/$', jsonrpc_site.dispatch, name='jsonrpc_mountpoint'),

#    url(r'^private_files/', include('private_files.urls')),
    url(r'^room/(?P<id>\d+)/ajax/$', jqchat.views.BasicAjaxHandler, name="jqchat_ajax"),

)
