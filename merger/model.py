import logging
import os
import re
import sys
import git

from .mixin import ComparableMixin
from .error import UnresolvedConflictsError

class Branch(ComparableMixin):
    _regex_minor = re.compile(r'(\d+)\.(\d+)')
    _branch = None

    _v_major = None

    @classmethod
    def create(cls, github_branch):
        if github_branch.name.isdecimal():  # it's major
            return MajorBranch(int(github_branch.name), github_branch)

        else:
            match = cls._regex_minor.fullmatch(github_branch.name)
            if not match:
                return None

            version = match.groups()
            return MinorBranch(int(version[0]), int(version[1]), github_branch)

    def __init__(self, github_branch):
        self._branch = github_branch

    def sameMajor(self, other):
        return self._v_major == other._v_major

    @property
    def name(self):
        return self._branch.name

class MajorBranch(Branch):
    def __init__(self, version, github_branch):
        super().__init__(github_branch)
        self._v_major = version

    def _cmpkey(self):
        return (self._v_major, sys.maxsize)

class MinorBranch(Branch):
    _v_minor = None

    def __init__(self, major_version, minor_version, github_branch):
        super().__init__(github_branch)
        self._v_major = major_version
        self._v_minor = minor_version

    def _cmpkey(self):
        return (self._v_major, self._v_minor)

class ProxyRepo:
    _target = None
    _github_repo = None
    _git_repo = None
    _branches = []
    _skip = []

    def __init__(self, target):
        self._target = target
        self._github_repo = target.github_repo

        _path = '/tmp/ss-merger-{}'.format(self._github_repo.id)

        logging.info('Checking out into %s', _path)

        if os.path.exists(_path):
            logging.warning('Folder already exists, skipping')
            self._git_repo = git.Repo(_path)
        else:
            self._git_repo = git.Repo.clone_from(self._github_repo.clone_url, _path)
            logging.info('Done')

        for github_branch in self._github_repo.get_branches():
            branch = Branch.create(github_branch)
            if not branch:
                continue
            if target.config('only') and str(branch._v_major) not in [str(v) for v in target.config('only')]:
                continue
            if branch.name in target.config('skip', []):
                continue
            self._branches.append(branch)

        self._branches.sort()
        logging.info('Identified merge-up branches: %s', [b.name for b in self._branches])

        self._git_repo_init()

    @property
    def branches(self):
        return self._branches

    @property
    def g_repo(self):
        return self._git_repo

    @property
    def gh_repo(self):
        return self._github_repo

    def _git_repo_init(self):
        origin = self._git_repo.remotes.origin
        origin.fetch()

        for branch in self.branches:
            try:
                self._git_repo.create_head(branch.name, origin.refs[branch.name].commit)
            except:
                pass

            if self._git_repo.heads[branch.name].commit != origin.refs[branch.name].commit:
                self._skip.append(branch.name)
                logging.warning('Skipping %s (different with origin; already merged-up?)', branch.name)

        if 'mergeup_fork' in self._git_repo.remotes:
            logging.info('Mergeup remote is %s', [i for i in self._git_repo.remote('mergeup_fork').urls][0])
        else:
            logging.info('Mergeup remote is %s', self._target.fork.github_repo.ssh_url)
            self._git_repo.create_remote('mergeup_fork', self._target.fork.github_repo.ssh_url)

    def mergeUp(self, conflict_resolvers):
        # import ipdb; ipdb.set_trace()
        idx = 1

        while len(self.branches) > idx+1:
            self._mergeUp(idx, conflict_resolvers)
            idx += 1

    def _mergeUp(self, idx, conflict_resolvers):
        src_branch = self.branches[idx]
        dst_branch = self.branches[idx+1]

        src = src_branch.name
        dst = dst_branch.name

        if dst in self._skip:
            return True;

        if not self._target.config('merge-majors', False) and not src_branch.sameMajor(dst_branch):
            logging.warning('Skipping merge {} to {}'.format(src, dst))
            return True

        mergeup_commit_message = 'Merge-up "{}" into "{}"'.format(src, dst)

        logging.info('%s', mergeup_commit_message)

        src_head = self._git_repo.heads[src]
        dst_head = self._git_repo.heads[dst]
        dst_head.checkout()

        dst_original_commit = dst_head.commit

        try:
            self._git_repo.git.merge(src_head, message=mergeup_commit_message, commit=True)

        except git.exc.GitCommandError as e:
            logging.warning('Conflict! %s', e.stdout)

            if len(self._git_repo.index.unmerged_blobs()):
                self._resolveConflicts(conflict_resolvers)
            else:
                raise Exception("Not sure what's wrong...")

            if len(self._git_repo.index.unmerged_blobs()):
                raise UnresolvedConflictsError()
                # raise Exception('Unresolved conflicts!')

            self._git_repo.git.commit(message=mergeup_commit_message)

        dst_mergeup_commit = self._git_repo.commit()

        if dst_mergeup_commit != dst_original_commit:
            self._pushMergedBranch(dst)
            self._pullRequestMergedBranch(dst)
        else:
            logging.info('Already up-to-date')

    def _resolveConflicts(self, conflict_resolvers):
        for resolver in conflict_resolvers:
            if resolver.isKnown(self._git_repo):
                try:
                    logging.warning('Running %s', resolver.name)
                    resolver.resolve(self._git_repo)
                except:
                    logging.exception('Resolver Failed')

    def _pushMergedBranch(self, dst_name):
        the_branch = 'merge-up/{}'.format(dst_name)

        self._git_repo.git.checkout(b=the_branch)

        logging.warning('Pushing %s to %s', the_branch, [i for i in self._git_repo.remote('mergeup_fork').urls][0])

        self._git_repo.git.push('mergeup_fork', the_branch)

        return True

    def _pullRequestMergedBranch(self, dst_name):
        the_branch = 'merge-up/{}'.format(dst_name)

        logging.warning('Creating a PR for %s', the_branch)

        self._target.fork.github_repo.create_pull(
            title=self._git_repo.branches[dst_name].commit.message,
            body='Created by the auto-merger ([RFC 9083](https://github.com/silverstripe/silverstripe-framework/issues/9083))',
            head=the_branch,
            base=dst_name
        )
