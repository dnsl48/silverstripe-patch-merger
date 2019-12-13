import docker
import os
import yaml

cfg_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config.yml')

with open(cfg_file) as f:
    config = yaml.load(f, yaml.SafeLoader)

# import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    from merger.core import Core
    from merger.model import ProxyRepo
    from merger.conflict_resolve.deleted import DeletedInNewerVersion
    from merger.conflict_resolve.node import NodeJsNaiveResolver

    core = Core(config)

    for target in core.get_targets():
        proxy_repo = ProxyRepo(target)

        proxy_repo.mergeUp([
            DeletedInNewerVersion(),
            NodeJsNaiveResolver(docker.client.from_env())
        ])

    print('Done!')