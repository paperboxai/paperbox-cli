"""Click helpers for the PBX CLI."""

from click import Option, UsageError, Group


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (
                " NOTE: This argument is mutually exclusive with " " arguments: [" + ex_str + "]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            used_mutually_exclusive_arguments = [
                para_item
                for para in [
                    param.opts
                    for param in ctx.command.params
                    if param.name in self.mutually_exclusive
                ]
                for para_item in para
            ]
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "argument(s) `{}`.".format(
                    ", ".join(self.opts + self.secondary_opts),
                    ", ".join(used_mutually_exclusive_arguments),
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


class GroupWithCommandOptions(Group):
    """Allow application of options to group with multi command"""

    def add_command(self, cmd, name=None):
        Group.add_command(self, cmd, name=name)

        # add the group parameters to the command
        for param in self.params:
            cmd.params.append(param)

        # hook the commands invoke with our own
        cmd.invoke = self.build_command_invoke(cmd.invoke)
        self.invoke_without_command = True

    def build_command_invoke(self, original_invoke):
        def command_invoke(ctx):
            """insert invocation of group function"""

            # separate the group parameters
            ctx.obj = dict(_params=dict())
            for param in self.params:
                name = param.name
                ctx.obj["_params"][name] = ctx.params[name]
                del ctx.params[name]

            # call the group function with its parameters
            params = ctx.params
            ctx.params = ctx.obj["_params"]
            self.invoke(ctx)
            ctx.params = params

            # now call the original invoke (the command)
            original_invoke(ctx)

        return command_invoke
