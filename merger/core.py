# from .model import Repo  # , Branch
# from .repo import get_repository
from github import Github

class Core:
    def __init__(self, config):
        self._config = config
        self._validateConfig()

        self._github = Github(self._config['github']['access_token'])

    def _validateConfig(self):
        if 'github' not in self._config:
            raise Exception("Config must define 'github' section")

        if 'access_token' not in self._config['github']:
            raise Exception("Config must define 'github.access_token'")

    @property
    def github(self):
        return self._github

    @property
    def config(self):
        return self._config

    def get_targets(self):
        for target_config in self._config['target']:
            yield Target(self, target_config)

class Target:
    def __init__(self, core, config):
        self._core = core
        self._fork = None
        self._github = core.github
        self._github_org = None
        self._github_repo = None
        self._configure(config)

    def _configure(self, config):
        if type(config) == str:
            self._configure_string(config)

        else:
            raise Exception('Unimplemented target configuration')

    def _configure_string(self, repository_address):
        '''Configure target from a string which would usually be a repository\n'''
        '''identifier, e.g. silverstripe/installer would target\n'''
        '\torg: silverstripe\n'
        '\trepo: installer'
        org_repo = repository_address.split('/', 1)

        if len(org_repo) != 2:
            raise Exception('Could not read target: {}'.format(org_repo))

        (org, repo) = org_repo

        self._github_org = self._github.get_user(org)
        self._github_repo = self._github_org.get_repo(repo)

        self._fork = Fork(self._core, self)

    @property
    def fork(self):
        return self._fork

    @property
    def github_repo(self):
        return self._github_repo

    @property
    def github_org(self):
        return self._github_org

class Fork:
    def __init__(self, core, target):
        self._core = core
        self._target = target
        self._github_org = target.github_org
        self._github_repo = target.github_repo

    @property
    def github_org(self):
        return self._github_org

    @property
    def github_repo(self):
        return self._github_repo