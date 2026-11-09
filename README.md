[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSenophyx%2Fdiscord-rpc&label=Visitors&countColor=%2337d67a&style=flat&labelStyle=none)](https://github.com/Senophyx/discord-rpc)
[![Discord](https://img.shields.io/discord/887650006977347594?label=EterNomm&logo=discord)](https://discord.gg/qpT2AeYZRN)
[![Total Downloads](https://static.pepy.tech/badge/discord-rpc)](https://pepy.tech/project/discord-rpc)
[![PyPI](https://img.shields.io/pypi/v/discord-rpc?label=PyPI%20Version&logo=pypi)](https://pypi.org/project/discord-rpc)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/Senophyx/discord-rpc?label=Commit%20Activity&logo=github)](https://github.com/Senophyx/discord-rpc)

# Discord RPC

<img src='media/preview.png' style='width: 30%;' alt='Dicord-RPC preview'>

A Python wrapper for the Discord RPC API that allows you to create your own custom Rich Presence.

[![Changelog](https://img.shields.io/badge/Changelog-blue?style=for-the-badge&logo=github)](CHANGELOG.md)
[![Documentation](https://img.shields.io/badge/Documentation-gray?style=for-the-badge&logo=googledocs&logoColor=white)](DOCS.md)

## Install
- PyPI
```
pip install discord-rpc
```

## Quick example
```py
import discordrpc

rpc = discordrpc.RPC(app_id=12345678910)

rpc.set_activity(
      state="A super simple rpc",
      details="simple RPC"
    )

# Required if you only run Discord RPC on this file or current instance.
rpc.run()
```
`rpc.run()` is only used if you are only running Discord RPC on the current file/instance. If there are other programs/tasks on the current instance, `rpc.run()` does not need to be used.

More examples [here](https://github.com/Senophyx/discord-rpc/tree/main/examples).


## Contributors
Big thanks for contributors who help this project keep updated, and maintained.

<a href="https://github.com/senophyx/discord-rpc/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=senophyx/discord-rpc&columns=5" />
</a>

<!-- Made with [contrib.rocks](https://contrib.rocks). -->

## Links
- [Github Repository](https://github.com/Senophyx/discord-rpc)
- [PyPI Project page](https://pypi.org/project/discord-rpc/)
- [TestPyPI Project page](https://test.pypi.org/project/discord-rpc/)
- [Discord Server](https://discord.gg/qpT2AeYZRN)
- [Initial commit](https://github.com/Senophyx/discord-rpc/commit/da720b6f95c541a412bb382620071f26c9e97471)

## Star History

<a href="https://www.star-history.com/?repos=senophyx%2Fdiscord-rpc&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=senophyx/discord-rpc&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=senophyx/discord-rpc&type=date&legend=top-left" />
   <img alt="discord-rpc star history chart" src="https://api.star-history.com/chart?repos=senophyx/discord-rpc&type=date&legend=top-left" />
 </picture>
</a>

## Licence & Copyright

```
This Project under MIT License
Copyright (c) 2021-2025 Senophyx
```