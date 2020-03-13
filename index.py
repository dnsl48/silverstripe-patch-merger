import docker
import os
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s\t%(message)s')

cfg_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config.yml')

with open(cfg_file) as f:
    logging.info('Reading config at: %s', cfg_file)
    config = yaml.load(f, yaml.SafeLoader)

# import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    from merger.core import Core
    from merger.error import UnresolvedConflictsError
    from merger.model import ProxyRepo
    from merger.conflict_resolve.deleted import DeletedInNewerVersion
    from merger.conflict_resolve.node import NodeJsNaiveResolver
    from merger.conflict_resolve.travisconfig import TravisConfigIgnorer

    core = Core(config)

    for target in core.get_targets():
        logging.info('Processing repository: %s', target.github_repo.full_name)

        try:
            proxy_repo = ProxyRepo(target)

            proxy_repo.mergeUp([
                TravisConfigIgnorer(),
                DeletedInNewerVersion(),
                NodeJsNaiveResolver(docker.client.from_env())
            ])
        except UnresolvedConflictsError:
            logging.error('Unresolved conflicts. Resolve manually and restart')
            exit()
        except:
            logging.exception('==== Error ====')
            exit()

    print('All done, congrats!')