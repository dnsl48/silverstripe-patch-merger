from github import Github
from .model import Repo

_gh = Github()
# _org = _gh.get_organization('silverstripe')
# _repo = org.get_repo('silverstripe-admin')
_org = _gh.get_user('dnsl48')


def get_repository(name):
    gh_repo = _org.get_repo('silverstripe-admin')
    if gh_repo:
        return Repo(gh_repo)