# -*- coding: utf-8 -*-
import urllib

from trac.core import Component, implements
from trac.web.api import IRequestFilter

from multiproject.common.projects import Project
from multiproject.core.configuration import conf
from multiproject.core.proto import ProtocolManager


class BrowserModifyModule(Component):
    """
    Adds checkout commands to browser
    """

    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'browser.html':
            username = urllib.quote(req.authname)
            scm = self.env.config.get('trac', 'repository_type')

            project = Project.get(self.env)

            names = {'git':'GIT', 'svn':'Subversion', 'hg':'Mercurial'}
            cmd_kinds = {'git':'Clone', 'hg':'Clone', 'svn':'Check out'}

            type = names[scm]
            schemes = self.protocols(project, scm)

            data['kinds'] = cmd_kinds
            data['schemes'] = schemes
            data['name'] = names[scm]
            data['type'] = scm

            co_commands = {}
            for scheme in schemes:
                co_commands[scheme] = self.create_co_command(scm, username, scheme)
            data['co_commands'] = co_commands

        return template, data, content_type

    def protocols(self, project, scm):
        protocol_manager = ProtocolManager(project.id)
        allowed = protocol_manager.allowed_protocols(scm)

        schemes = []
        for proto in ProtocolManager.available_schemes(scm):
            if proto in allowed:
                schemes.append(proto)
        return schemes

    def create_co_command(self, scm, username, scheme):
        if scheme == 'ssh':
            scm = 'gitssh'

        params = {'scheme': scheme,
                  'username': username,
                  'domain': conf.domain_name,
                  'scm': scm,
                  'project': conf.resolveProjectName(self.env)}

        # username was taken from use because of problems resolving nokia account id
        co_commands = {}
        co_commands['git'] = 'git clone %(scheme)s://%(domain)s/%(scm)s/%(project)s.git'
        co_commands['gitssh'] = 'git clone %(scheme)s://git@%(domain)s/%(project)s.git'
        co_commands['svn'] = 'svn co %(scheme)s://%(domain)s/%(scm)s/%(project)s'
        co_commands['hg'] = 'hg clone %(scheme)s://%(domain)s/%(scm)s/%(project)s'

        return co_commands[scm] % params
