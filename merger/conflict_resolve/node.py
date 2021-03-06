# resolve conflicts with javascript bundles (looking for /client/dist/js/bundle.js)

import json
import logging
import os

from . import ConflictResolver

class NodeJsNaiveResolver(ConflictResolver):
    '''
    Trying to resolve conflicts around JavaScript bundles.
    Follows the convention that the bundles must be placed in "client/dist/".
    Recognizes the conflict by looking for 'client/dist/js/bundle.js' file
    '''

    _docker_client = None

    def __init__(self, docker_client):
        try:
            docker_client.ping()
        except:
            logging.exception('Could not connect to Docker')
            raise

        self._docker_client = docker_client

    def getNodeVersion(self, git_repo):
        node_version = None
        wdir = git_repo.working_dir
        nvmrc = os.path.join(wdir, '.nvmrc')
        pjson = os.path.join(wdir, 'package.json')

        if os.path.exists(nvmrc):
            with open(nvmrc, 'r') as f:
                try:
                    node_version = int(f.read().strip())
                except:
                    pass

        if not node_version:
            if not os.path.exists(pjson):
                return None

        with open(pjson, 'r') as f:
            data = json.load(f)

        if not data or 'engines' not in data.keys() or 'node' not in data['engines']:
            return None

        raw_version = data['engines']['node'].strip('^').split('.')
        if len(raw_version):
            try:
                node_version = int(raw_version[0])
            except:
                pass

        return node_version

    def isKnown(self, git_repo):
        if 'client/dist/js/bundle.js' not in git_repo.index.unmerged_blobs().keys():
            return False

        if not self.getNodeVersion(git_repo):
            return False

        return True

    def resolve(self, git_repo):
        super().resolve(git_repo)

        wdir = git_repo.working_dir

        node_version = self.getNodeVersion(git_repo)
        logging.info('Identified node version: %s', node_version)
        node_image = 'node:{}'.format(node_version)
        logging.info('Pulling docker image: %s', node_image)

        self._docker_client.images.pull(node_image)

        logging.info('Running: "yarn && yarn build"')
        result = self._docker_client.containers.run(
            node_image,
            r'bash -lc "cd /app/ && yarn && yarn build && echo SUCCESSFUL_BUILD"',
            user=os.geteuid(),
            volumes={wdir: {
                'bind': '/app',
                'mode': 'rw'
            }}
        ).decode('utf8').strip().split('\n')

        if result[-1] == 'SUCCESSFUL_BUILD':
            logging.info('Successful build; Running: git add client/dist/')
            git_repo.git.add('client/dist/')
            return True
        else:
            logging.error('Build failed: %s', result)
            return False